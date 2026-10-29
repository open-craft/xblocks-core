/* Matching game isolated script */
function GamesXBlockMatchingInit(runtime, element) {
    const pagesEl = $(element).find('#matching-pages-data');
    const pages = JSON.parse(pagesEl.text());
    pagesEl.remove();

    const container = $('.gamesxblock-matching', element);
    const has_timer = $(container).data('timed') === true || $(container).data('timed') === 'true';

    if (!container.length || !pages || pages.length === 0) return;

    var $liveRegion = $(element).find('#matching-sr-announcements');

    function announce(message) {
        var el = $liveRegion[0];
        el.textContent = '';
        // Force reflow so the screen reader registers the cleared state
        void el.offsetHeight;
        el.textContent = message;
    }

    // Prevent duplicate init that would attach multiple handlers
    if (container.data('gx_matching_initialized')) {
        return;
    }
    container.data('gx_matching_initialized', true);

    let allPages = pages;
    let currentPageIndex = 0;
    let totalPages = pages.length;

    let timerInterval = null;
    let timeSeconds = 0;
    const isPreviewMode = new URLSearchParams(window.location.search).get('preview') === '1';

    function formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        }
        return `${minutes}:${String(secs).padStart(2, '0')}`;
    }

    function startTimer() {
        if (timerInterval) return;

        timerInterval = setInterval(function() {
            timeSeconds++;
            $('#matching-timer', element).text(formatTime(timeSeconds));
        }, 1000);
    }

    function stopTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    }

    function refreshGame() {
        if (isPreviewMode) {
            currentPageIndex = 0;
            matchCount = 0;
            firstSelection = null;
            timeSeconds = 0;
            stopTimer();
            $('.matching-end-screen', element).removeClass('active');
            $('.matching-new-best', element).removeClass('active');
            $('.matching-grid', element).show().addClass('active');
            $('.matching-footer', element).show().addClass('active');
            $('#matching-timer', element).text('0:00');
            const page = allPages[0];
            currentPagePairs = page.left_items.length;
            updateProgress();
            $('.matching-column-left', element).empty();
            $('.matching-column-right', element).empty();
            page.left_items.forEach(function(item) {
                const wrapper = $('<div class="matching-box-wrapper"></div>');
                const box = $('<div class="matching-box"></div>')
                    .attr('data-item-type', 'term').attr('data-match', item.match)
                    .attr('title', item.text).attr('role', 'button').attr('tabindex', '0');
                box.append($('<span class="matching-box-text"></span>').text(item.text));
                wrapper.append(box);
                $('.matching-column-left', element).append(wrapper);
            });
            page.right_items.forEach(function(item) {
                const wrapper = $('<div class="matching-box-wrapper"></div>');
                const box = $('<div class="matching-box"></div>')
                    .attr('data-item-type', 'definition').attr('data-hash', item.hash)
                    .attr('title', item.text).attr('role', 'button').attr('tabindex', '0');
                box.append($('<span class="matching-box-text"></span>').text(item.text));
                wrapper.append(box);
                $('.matching-column-right', element).append(wrapper);
            });
            attachBoxClickHandlers();
            if (has_timer) { startTimer(); }
            $('.matching-box', element).first().focus();
            return;
        }
        $.ajax({
            type: 'GET',
            url: runtime.handlerUrl(element, 'refresh_game'),
            dataType: 'html',
            success: function(html) {
                $(element).html(html);
                GamesXBlockMatchingInit(runtime, element);
                setTimeout(function() {
                    $('.matching-start-button', element).click();
                }, 100);
            },
            error: function(xhr, status, error) {
                console.error('Failed to refresh game:', error);
                window.location.reload();
            }
        });
    }

    $('.matching-start-button', element).off('click').on('click', function() {
        if (allPages && allPages[currentPageIndex]) {
            currentPagePairs = allPages[currentPageIndex].left_items.length;
        }

        $('.matching-start-screen', element).remove();
        $('.matching-grid', element).addClass('active');
        $('.matching-footer', element).addClass('active');

        if (has_timer) {
            startTimer();
        }
        setTimeout(function() {
            $('.matching-box', element).first().focus();
        }, 100);
    });

    $('.matching-end-button', element).off('click').on('click', function() {
        refreshGame();
    });

    let firstSelection = null;
    let matchCount = 0;
    let currentPagePairs = 0;

    function computeCircumference() {
        const circleEl = $('.matching-progress-bar', element)[0];
        if (!circleEl) return 0;
        const r = parseFloat(circleEl.getAttribute('r')) || 0;
        const svg = circleEl.ownerSVGElement;
        if (!svg) return 2 * Math.PI * r;
        const vbHeight = svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal.height : r * 2;
        const renderedHeight = svg.getBoundingClientRect().height || vbHeight;
        const scale = vbHeight ? (renderedHeight / vbHeight) : 1;
        const effectiveR = r * scale;
        return 2 * Math.PI * effectiveR;
    }

    const baseCircumference = computeCircumference();
    if (baseCircumference) {
        $('.matching-progress-bar', element).css({
            'stroke-dasharray': baseCircumference,
            'stroke-dashoffset': baseCircumference
        });
    }

    function updateProgress() {
        const currentPageNumber = currentPageIndex + 1;
        $('#matching-progress-count').text(currentPageNumber);
        const progress = totalPages > 0 ? (currentPageNumber / totalPages) : 0;
        const circumference = baseCircumference || computeCircumference();
        const offset = circumference * (1 - progress);
        $('.matching-progress-bar', element).css('stroke-dashoffset', offset);
    }
    updateProgress();

    function clearSelectionVisual(box) {
        box.removeClass('selected incorrect');
        box.attr('aria-pressed', 'false');
    }

    function markIncorrect(a, b) {
        a.addClass('incorrect');
        b.addClass('incorrect');
        announce('Incorrect match. Try again.');
        setTimeout(() => {
            clearSelectionVisual(a);
            clearSelectionVisual(b);
        }, 600);
    }

    function loadNextPage() {
        // Increment page index
        currentPageIndex += 1;
        updateProgress();

        // Reset match count for new page
        matchCount = 0;
        firstSelection = null;

        // Get next page data
        const nextPage = allPages[currentPageIndex];
        if (!nextPage) return;

        currentPagePairs = nextPage.left_items.length;

        // Clear current boxes
        $('.matching-column-left', element).empty();
        $('.matching-column-right', element).empty();

        // Render left items
        nextPage.left_items.forEach(item => {
            const wrapper = $('<div class="matching-box-wrapper"></div>');
            const box = $('<div class="matching-box"></div>')
                .attr('data-item-type', 'term')
                .attr('data-match', item.match)
                .attr('title', item.text)
                .attr('role', 'button')
                .attr('tabindex', '0');
            const text = $('<span class="matching-box-text"></span>').text(item.text);
            box.append(text);
            wrapper.append(box);
            $('.matching-column-left', element).append(wrapper);
        });

        // Render right items
        nextPage.right_items.forEach(item => {
            const wrapper = $('<div class="matching-box-wrapper"></div>');
            const box = $('<div class="matching-box"></div>')
                .attr('data-item-type', 'definition')
                .attr('data-hash', item.hash)
                .attr('title', item.text)
                .attr('role', 'button')
                .attr('tabindex', '0');
            const text = $('<span class="matching-box-text"></span>').text(item.text);
            box.append(text);
            wrapper.append(box);
            $('.matching-column-right', element).append(wrapper);
        });

        // Re-attach click handlers to new boxes
        attachBoxClickHandlers();
        $('.matching-box', element).first().focus();
        announce('Page ' + (currentPageIndex + 1) + ' of ' + totalPages);
    }

    function markMatch(a, b) {
        a.addClass('matched').removeClass('selected');
        b.addClass('matched').removeClass('selected');
        announce('Correct match!');
        matchCount += 1;

        // Delay aria state changes so VoiceOver finishes reading "Correct match!" first
        setTimeout(function() {
            a.attr('aria-disabled', 'true').attr('aria-pressed', 'false');
            b.attr('aria-disabled', 'true').attr('aria-pressed', 'false');
        }, 1500);

        // Check if current page is complete
        if (matchCount >= currentPagePairs) {
            // Check if there are more pages
            if (currentPageIndex + 1 < totalPages) {
                // Delay so "Correct match!" is heard before "Page X of Y"
                setTimeout(function() {
                    loadNextPage();
                }, 1500);
            } else {
                // All pages complete - end game
                if (has_timer) {
                    stopTimer();
                }
                // Delay so "Correct match!" is heard before "Congratulations"
                setTimeout(() => {
                    completeGame();
                }, 1500);
            }
            return;
        }

        // Determine next focus target before boxes are removed from the DOM.
        // Look for the nearest unmatched box after the last clicked box (b),
        // then before it in the same column, then any remaining unmatched box.
        var $nextFocus = b.parent().nextAll('.matching-box-wrapper')
            .find('.matching-box:not(.matched)').first();
        if (!$nextFocus.length) {
            $nextFocus = b.parent().prevAll('.matching-box-wrapper')
                .find('.matching-box:not(.matched)').first();
        }
        if (!$nextFocus.length) {
            $nextFocus = $('.matching-box:not(.matched)', element).first();
        }

        setTimeout(() => {
            $([a, b]).each(function() {
                $(this).fadeOut(600, function() {
                    $(this).remove();
                });
            });
            setTimeout(function() {
                if ($nextFocus.length) {
                    $nextFocus.focus();
                }
            }, 650);
        }, 1500);
    }

    function completeGame() {
        if (!has_timer) {
            $('.matching-end-screen', element).addClass('active');
            $('.matching-non-timer', element).addClass('active');
            $('.matching-new-best', element).remove();
            $('.matching-prev-best', element).remove();
            $('.matching-grid', element).remove();
            $('.matching-footer', element).remove();
            if (typeof GamesConfetti !== 'undefined') {
                GamesConfetti.trigger($('.confetti-container', element), 20);
            }
            announce('Congratulations! You matched all items.');
            $('.matching-end-screen-content', element).focus();
            return;
        }

        if (isPreviewMode) {
            $('.matching-end-screen', element).addClass('active');
            $('.matching-new-best', element).addClass('active');
            $('.matching-grid', element).hide();
            $('.matching-footer', element).hide();
            $('#matching-current-result', element).text(formatTime(timeSeconds));
            if (typeof GamesConfetti !== 'undefined') {
                GamesConfetti.trigger($('.confetti-container', element), 20);
            }
            announce('Congratulations! You matched all items.');
            $('.matching-end-screen-content', element).focus();
            return;
        }

        $.ajax({
            type: 'POST',
            url: runtime.handlerUrl(element, 'complete_matching_game'),
            data: JSON.stringify({ new_time: has_timer ? timeSeconds : null }),
            contentType: 'application/json',
            dataType: 'json',
            success: function(response) {
                // response is { new_time: int, prev_best_time: int or null }
                // if new_time is less than prev_best_time, it's a new record
                // if prev_best_time is null, it's the first completed game
                // if prev_best_time is not null and new_time >= prev_best_time, no new record

                $('.matching-end-screen', element).addClass('active');
                $('.matching-grid', element).remove();
                $('.matching-footer', element).remove();
                const { new_time, prev_best_time } = response;
                if (prev_best_time === null || new_time < prev_best_time) {
                    $('.matching-new-best', element).addClass('active');
                    $('.matching-prev-best', element).remove();
                    $('#matching-current-result', element).text(formatTime(new_time));
                    if (prev_best_time !== null) {
                        $('.matching-new-prev-best', element).addClass('active');
                        $('#matching-prev-best', element).text(formatTime(prev_best_time));
                    }
                } else {
                    $('.matching-new-best', element).remove();
                    $('.matching-prev-best', element).addClass('active');
                    $('#matching-personal-best-time', element).text(formatTime(prev_best_time));
                    $('#matching-prev-current-best-time', element).text(formatTime(new_time));
                }

                if (typeof GamesConfetti !== 'undefined') {
                    GamesConfetti.trigger($('.confetti-container', element), 20);
                }
                announce('Congratulations! You matched all items.');
                $('.matching-end-screen-content', element).focus();
            },
            error: function(xhr, status, error) {
                console.error('Failed to submit score:', error);
            }
        });
    }

    function handleBoxClick() {
        const box = $(this);
        if (box.hasClass('matched')) return;
        const type = box.data('itemType');

        if (firstSelection && firstSelection[0].is(box)) {
            clearSelectionVisual(box);
            firstSelection = null;
            return;
        }

        if (firstSelection && firstSelection[1] === type) {
            clearSelectionVisual(firstSelection[0]);
            firstSelection = null;
        }

        box.addClass('selected');
        box.attr('aria-pressed', 'true');
        if (!firstSelection) {
            firstSelection = [box, type];
            return;
        }

        const [prevBox, prevType] = firstSelection;
        firstSelection = null;
        const termBox = prevType === 'term' ? prevBox : box;
        const defBox  = prevType === 'term' ? box : prevBox;
        const defHash      = String(defBox.data('hash')).trim();
        const expectedHash = String(termBox.data('match')).trim();

        if (expectedHash === defHash) {
            markMatch(termBox, defBox);
        } else {
            const termText = termBox.find('.matching-box-text').text().trim();
            let resolvedTerm = null;
            $('.matching-box[data-item-type="term"]', element).not('.matched').each(function() {
                const $t = $(this);
                if ($t.find('.matching-box-text').text().trim() === termText
                        && String($t.data('match')).trim() === defHash) {
                    resolvedTerm = $t;
                    return false; // break
                }
            });

            if (resolvedTerm) {
                resolvedTerm.attr('data-match', expectedHash).data('match', expectedHash);
                markMatch(termBox, defBox);
            } else {
                markIncorrect(termBox, defBox);
            }
        }
    }

    function attachBoxClickHandlers() {
        $('.matching-box', element).off('click keydown')
            .on('click', handleBoxClick)
            .on('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleBoxClick.call(this);
                }
            });
    }

    attachBoxClickHandlers();

    // Set initial focus on the start button so keyboard users land on the game
    $('.matching-start-button', element).focus();
}

