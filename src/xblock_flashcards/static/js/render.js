function FlashCardsXBlock(runtime, element, data) {
    (async () => {
        const { renderBlock } = await import(data.url);
        renderBlock(element, runtime, data.data);
    })();
}
