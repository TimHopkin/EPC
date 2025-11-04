#!/usr/bin/env node

// Simple deployment validation script
const fs = require('fs');
const path = require('path');

console.log('🔍 EPC Data Explorer - Deployment Check');
console.log('=====================================');

// Check required files
const requiredFiles = [
    'index.html',
    'package.json', 
    'netlify.toml',
    '_redirects',
    '.nvmrc'
];

let allFilesExist = true;

requiredFiles.forEach(file => {
    if (fs.existsSync(file)) {
        console.log(`✅ ${file} - Found`);
    } else {
        console.log(`❌ ${file} - Missing`);
        allFilesExist = false;
    }
});

// Check index.html content
if (fs.existsSync('index.html')) {
    const indexContent = fs.readFileSync('index.html', 'utf8');
    if (indexContent.includes('EPC Data Explorer')) {
        console.log('✅ index.html - Contains EPC content');
    } else {
        console.log('❌ index.html - Missing EPC content');
        allFilesExist = false;
    }
}

// Check package.json
if (fs.existsSync('package.json')) {
    try {
        const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
        if (pkg.scripts && pkg.scripts.build) {
            console.log('✅ package.json - Build script present');
        } else {
            console.log('❌ package.json - Missing build script');
            allFilesExist = false;
        }
    } catch (e) {
        console.log('❌ package.json - Invalid JSON');
        allFilesExist = false;
    }
}

console.log('\n🎯 Deployment Status:');
if (allFilesExist) {
    console.log('✅ Ready for Netlify deployment!');
    console.log('\n📋 Next steps:');
    console.log('1. Push to GitHub');
    console.log('2. Netlify will auto-deploy');
    console.log('3. Access your live EPC Data Explorer');
} else {
    console.log('❌ Deployment issues detected');
    console.log('Please fix the missing files above');
}

console.log('\n🌐 Expected Features:');
console.log('• Dashboard with EPC statistics');  
console.log('• Advanced search (postcode, UPRN, local authority)');
console.log('• Interactive analytics charts');
console.log('• CSV & GeoJSON export');
console.log('• API credential management');
console.log('• Responsive design');

process.exit(allFilesExist ? 0 : 1);