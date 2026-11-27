function FlashCardsXBlock(runtime, element, data) {
    (async () => {
        const { renderBlock } = await import(data.url);
        renderBlock(runtime, element, data);
    })();
}
