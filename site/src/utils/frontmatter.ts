import type { RehypePlugin } from '@astrojs/markdown-remark';

// Wrap tables in a horizontally scrollable, keyboard-focusable region.
export const responsiveTablesRehypePlugin: RehypePlugin = () => {
  return function (tree) {
    if (!tree.children) return;

    for (let i = 0; i < tree.children.length; i++) {
      const child = tree.children[i];

      if (child.type === 'element' && child.tagName === 'table') {
        tree.children[i] = {
          type: 'element',
          tagName: 'div',
          properties: {
            className: ['table-scroll'],
            tabIndex: 0,
            role: 'region',
            ariaLabel: 'Table',
          },
          children: [child],
        };

        i++;
      }
    }
  };
};
