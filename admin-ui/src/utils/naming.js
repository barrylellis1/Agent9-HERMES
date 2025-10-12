// Utility functions to help with naming conventions and conflicts

// Material-UI reserved names
const MATERIAL_UI_RESERVED = [
  'AppBar', 'Button', 'Card', 'CardContent', 'CardHeader',
  'Checkbox', 'Chip', 'Dialog', 'Drawer', 'Grid',
  'IconButton', 'Input', 'List', 'ListItem', 'Menu',
  'Paper', 'Select', 'Snackbar', 'Table', 'TextField',
  'Toolbar', 'Typography',
];

// UI Component naming patterns
const UI_PATTERNS = {
  // Main component types
  Pages: ['Page', 'View'],
  Forms: ['Form', 'Input'],
  Tables: ['Table', 'Grid'],
  Lists: ['List', 'Collection'],
  Panels: ['Panel', 'Section'],
  Modules: ['Module', 'Component'],
  
  // Common UI patterns
  Views: ['View', 'Display'],
  Controls: ['Control', 'Manager'],
  Handlers: ['Handler', 'Processor'],
  Managers: ['Manager', 'Controller']
};

// Naming rules for UI components
const NAMING_RULES = {
  usePascalCase: true,
  useA9Prefix: true,
  
  // Component-specific rules
  components: {
    prefix: 'A9_',
    suffix: '',
    useTeamPrefix: true
  },
  
  // File naming rules
  files: {
    useKebabCase: true,
    includeExtension: true,
    useIndexFile: true
  }
};

export function isMaterialUIComponent(name) {
  return MATERIAL_UI_RESERVED.includes(name);
}

export function suggestAlternativeName(name) {
  if (isMaterialUIComponent(name)) {
    return `A9_${name}`;
  }
  return name;
}

export function validateComponentName(name) {
  if (isMaterialUIComponent(name)) {
    throw new Error(`Cannot use Material-UI component name: ${name}`);
  }
  return true;
}

// Usage examples:
// const componentName = validateComponentName('Card'); // Throws error
// const componentName = suggestAlternativeName('Card'); // Returns "A9_Card"
// const componentName = validateComponentName('A9_Card'); // Returns true
