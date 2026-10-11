import { getPermalink } from './utils/permalinks';

export const GITHUB_URL = 'https://github.com/7empestx/open-data-ml';
export const EMAIL = 'hello@beehivewebstudio.com';

// Sidebar for the long-form windml and policy pages (DocsLayout).
export const docsNav = [
  {
    title: 'windml',
    links: [
      { text: 'Overview', href: getPermalink('/windml') },
      { text: 'Results', href: getPermalink('/windml/results') },
      { text: 'Sample condition report', href: getPermalink('/windml/condition-report') },
      { text: 'Reproduce it', href: getPermalink('/windml/reproduce') },
      { text: 'Data sources and licenses', href: getPermalink('/windml/data-sources') },
      { text: 'Cleaning notes and data problems', href: getPermalink('/windml/cleaning') },
      { text: 'Failure labels', href: getPermalink('/windml/labels') },
    ],
  },
  {
    title: 'open-data-ml',
    links: [
      { text: 'Work with us', href: getPermalink('/work-with-us') },
      { text: 'About and data policy', href: getPermalink('/about') },
      { text: 'Roadmap', href: getPermalink('/roadmap') },
    ],
  },
];

export const headerData = {
  links: [
    {
      text: 'windml',
      links: docsNav[0].links,
    },
    { text: 'Results', href: getPermalink('/windml/results') },
    { text: 'Work with us', href: getPermalink('/work-with-us') },
    { text: 'About', href: getPermalink('/about') },
  ],
  iconLinks: [
    { ariaLabel: 'GitHub repository', icon: 'tabler:brand-github', href: GITHUB_URL },
    { ariaLabel: `Email ${EMAIL}`, icon: 'tabler:mail', href: `mailto:${EMAIL}` },
  ],
};

export const footerData = {
  links: [
    {
      title: 'windml',
      links: [
        { text: 'Overview', href: getPermalink('/windml') },
        { text: 'Results', href: getPermalink('/windml/results') },
        { text: 'Reproduce it', href: getPermalink('/windml/reproduce') },
      ],
    },
    {
      title: 'Data',
      links: [
        { text: 'Data sources and licenses', href: getPermalink('/windml/data-sources') },
        { text: 'Cleaning notes', href: getPermalink('/windml/cleaning') },
        { text: 'Failure labels', href: getPermalink('/windml/labels') },
      ],
    },
    {
      title: 'Company',
      links: [
        { text: 'Work with us', href: getPermalink('/work-with-us') },
        { text: 'About and data policy', href: getPermalink('/about') },
        { text: 'Roadmap', href: getPermalink('/roadmap') },
      ],
    },
  ],
  secondaryLinks: [
    { text: 'Data policy', href: getPermalink('/about') },
    { text: 'Contact', href: `mailto:${EMAIL}` },
  ],
  socialLinks: [
    { ariaLabel: 'GitHub repository', icon: 'tabler:brand-github', href: GITHUB_URL },
    { ariaLabel: `Email ${EMAIL}`, icon: 'tabler:mail', href: `mailto:${EMAIL}` },
  ],
  footNote: `open-data-ml by Beehive AI Labs LLC. Code under the <a class="underline" href="${GITHUB_URL}/blob/main/LICENSE">MIT license</a>. Kelmarsh and Penmanshiel data by Cubico Sustainable Investments Ltd, <a class="underline" href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Site based on the <a class="underline" href="https://github.com/arthelokyo/astrowind">AstroWind</a> template (MIT).`,
};
