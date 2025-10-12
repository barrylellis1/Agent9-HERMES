import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Import our naming utility
import { suggestAlternativeName, isMaterialUIComponent } from './naming.js';

// Configuration
const CONFIG = {
  excludeFiles: ['node_modules', '.git', 'dist', 'build'],
  excludePatterns: ['^A9_'], // Don't rename components that already have A9_ prefix
  dryRun: false, // Set to true to preview changes without making them
};

// Get all component files in a directory
async function getComponentFiles(dir) {
  const files = [];
  const dirents = await fs.promises.readdir(dir, { withFileTypes: true });
  
  for (const dirent of dirents) {
    const res = path.resolve(dir, dirent.name);
    
    // Skip excluded directories
    if (dirent.isDirectory() && 
        !CONFIG.excludeFiles.includes(path.basename(dirent.name))) {
      files.push(...await getComponentFiles(res));
    } else if (dirent.name.endsWith('.js')) {
      files.push(res);
    }
  }
  return files;
}

// Get all component names in a file
function getComponentNames(content) {
  const componentRegex = /\b([A-Z][a-zA-Z0-9]*)\b/g;
  const names = new Set();
  let match;
  
  while ((match = componentRegex.exec(content)) !== null) {
    const componentName = match[0];
    
    // Skip if it matches any exclude patterns
    if (CONFIG.excludePatterns.some(pattern => 
        new RegExp(pattern).test(componentName))) {
      continue;
    }
    
    // Skip Material-UI components
    if (isMaterialUIComponent(componentName)) {
      continue;
    }
    
    names.add(componentName);
  }
  
  return Array.from(names);
}

// Get suggested new names for components
function getSuggestedNames(componentNames) {
  return componentNames.reduce((acc, name) => {
    const newName = suggestAlternativeName(name, 'Components');
    if (newName !== name) {
      acc[name] = newName;
    }
    return acc;
  }, {});
}

// Generate a preview of changes
function generatePreview(file, content, suggestedNames) {
  const preview = {
    file,
    changes: [],
    originalContent: content
  };
  
  // Find and record all changes
  Object.entries(suggestedNames).forEach(([oldName, newName]) => {
    const regex = new RegExp(`\\b${oldName}\\b`, 'g');
    const matches = content.match(regex) || [];
    
    if (matches.length > 0) {
      preview.changes.push({
        oldName,
        newName,
        count: matches.length
      });
    }
  });
  
  return preview;
}

// Apply changes to content
function applyChanges(content, suggestedNames) {
  let newContent = content;
  Object.entries(suggestedNames).forEach(([oldName, newName]) => {
    newContent = newContent.replace(
      new RegExp(`\\b${oldName}\\b`, 'g'),
      newName
    );
  });
  return newContent;
}

// Process a single file
async function processFile(filePath, content) {
  const componentNames = getComponentNames(content);
  const suggestedNames = getSuggestedNames(componentNames);
  
  if (Object.keys(suggestedNames).length === 0) {
    console.log(`No changes needed for: ${filePath}`);
    return;
  }
  
  const preview = generatePreview(filePath, content, suggestedNames);
  
  if (CONFIG.dryRun) {
    console.log('\n=== DRY RUN ===');
    console.log(`File: ${filePath}`);
    console.log('Proposed changes:');
    preview.changes.forEach(change => {
      console.log(`- ${change.oldName} -> ${change.newName} (${change.count} occurrences)`);
    });
    return;
  }
  
  try {
    const newContent = applyChanges(content, suggestedNames);
    await fs.promises.writeFile(filePath, newContent, 'utf-8');
    console.log(`Updated: ${filePath}`);
    console.log('Changes applied:');
    preview.changes.forEach(change => {
      console.log(`- ${change.oldName} -> ${change.newName} (${change.count} occurrences)`);
    });
  } catch (error) {
    console.error(`Error updating ${filePath}:`, error);
  }
}

// Main function to rename components in a directory
export async function renameComponentsInDirectory(directory, options = {}) {
  try {
    // Update configuration with options
    Object.assign(CONFIG, options);
    
    console.log('Starting component renaming...');
    console.log('Dry run mode:', CONFIG.dryRun);
    console.log('Excluded files:', CONFIG.excludeFiles);
    console.log('Excluded patterns:', CONFIG.excludePatterns);
    
    const files = await getComponentFiles(directory);
    
    for (const file of files) {
      try {
        const content = await fs.promises.readFile(file, 'utf-8');
        await processFile(file, content);
      } catch (error) {
        console.error(`Error processing ${file}:`, error);
      }
    }
    
    console.log('\nComponent renaming complete!');
  } catch (error) {
    console.error('Error renaming components:', error);
  }
}

// Example usage:
// Rename components with dry run (preview changes)
// renameComponentsInDirectory(path.join(__dirname, '../components'), { dryRun: true });

// Rename components for real
// renameComponentsInDirectory(path.join(__dirname, '../components'));
