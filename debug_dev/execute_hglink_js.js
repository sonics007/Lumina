// HGLink main.js executor - extracts redirect URL
const fs = require('fs');

// Read the main.js file
const mainJs = fs.readFileSync('hglink_main_full.js', 'utf8');

// Mock window object to capture redirect
let capturedURL = null;
const window = {
    location: {
        get href() { return 'https://hglink.to/e/124fixrcqqxb'; },
        set href(url) {
            capturedURL = url;
            console.log('REDIRECT URL:', url);
        }
    }
};

// Mock document
const document = {
    location: window.location
};

try {
    // Execute the main.js code
    eval(mainJs);

    // Give it a moment to execute
    console.log('Evaluating JS...');
    setTimeout(() => {
        if (capturedURL) {
            console.log('\n✓ SUCCESS!');
            console.log('Final URL:', capturedURL);

            // Save to file
            fs.writeFileSync('hglink_redirect_url.txt', capturedURL);
            console.log('Saved to: hglink_redirect_url.txt');
        } else {
            console.log('\n✗ No redirect captured');
            console.log('The script may need browser-specific APIs');
        }
        process.exit(0);
    }, 2000);

} catch (error) {
    console.error('Error executing main.js:', error.message);
    console.error('\nThis means main.js requires browser APIs we cannot mock.');
    console.error('Trying alternative approach...');

    // Alternative: extract domains from arrays
    const dmcaMatch = mainJs.match(/const dmca=\[(.*?)\]/s);
    const mainMatch = mainJs.match(/const main=\[(.*?)\]/s);

    if (mainMatch) {
        console.log('\nFound main array, extracting domains...');
        // This would need more sophisticated parsing
        console.log('Main array content (first 500 chars):');
        console.log(mainMatch[1].substring(0, 500));
    }

    process.exit(1);
}
