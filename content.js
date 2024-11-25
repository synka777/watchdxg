Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
console.log("Extension script is running!");
