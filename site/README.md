# ml.beehivewebstudio.com

Source for the open-data-ml website, built with [Astro Starlight](https://starlight.astro.build) as a fully static site (no server, no analytics, no third-party scripts).

## Develop

Needs Node.js 22.12 or newer.

```bash
cd site
npm ci
npm run dev       # local preview at http://localhost:4321
npm run build     # static output in dist/
```

## Layout

- `src/content/docs/`: one Markdown or MDX file per page. The file path is the URL.
- `src/assets/condition-report/`: report figures, converted to WebP at build time.
- `src/components/BarChart.astro`: small HTML and CSS bar chart used on the results page (no JavaScript).
- `public/`: files copied as-is (favicon, social image, robots.txt, the sample report PDF).
- `astro.config.mjs`: site title, sidebar, header links and meta tags.

Numbers on the site come from `projects/windml/RESULTS.md` and `projects/windml/reports/`. Update them together.

## Deploy

Hosted on S3 behind CloudFront. See [DEPLOY.md](DEPLOY.md). Deploys are run manually by the site owner.
