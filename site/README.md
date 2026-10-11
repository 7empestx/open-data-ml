# ml.beehivewebstudio.com

Source for the open-data-ml website: open-data-ml by Beehive AI Labs LLC. Built with [Astro](https://astro.build) and [Tailwind CSS](https://tailwindcss.com), based on the [AstroWind](https://github.com/arthelokyo/astrowind) template (MIT, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)).

Fully static output: no server, no adapter, no analytics, no third-party scripts, and no remote fonts or images (Inter is self-hosted from `src/assets/fonts`).

## Develop

Needs Node.js 22.22.3 or newer (AstroWind's minimum).

```bash
cd site
npm ci
npm run dev       # local preview at http://localhost:4321
npm run build     # static output in dist/
```

## Layout

- `src/pages/index.astro`, `src/pages/work-with-us.astro`: landing pages built from AstroWind widgets (hero, stats, features, steps, FAQ, call to action).
- `src/content/docs/`: long-form pages (windml docs, about, roadmap) in Markdown or MDX. The file path is the URL. They render through `src/pages/[...slug].astro` and `src/layouts/DocsLayout.astro` (sidebar, table of contents, previous and next links).
- `src/navigation.ts`: header, footer and docs sidebar links, plus the GitHub and email links.
- `src/config.yaml`: site name, URL, default title, description and social image.
- `src/components/CustomStyles.astro`: brand colours. `src/assets/styles/tailwind.css`: global styles.
- `src/components/BarChart.astro`: HTML and CSS bar chart used on the results page (no JavaScript).
- `src/assets/condition-report/`: report figures, converted to WebP at build time.
- `public/`: files copied as-is (favicons, social image, robots.txt, the sample report PDF).

Numbers on the site come from `projects/windml/RESULTS.md` and `projects/windml/reports/`. Update them together.

## Deploy

Hosted on S3 behind CloudFront. See [DEPLOY.md](DEPLOY.md). Deploys are run manually by the site owner.
