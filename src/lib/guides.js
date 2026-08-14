// Localized datasets for editor-written static content (guides + glossary).
// Translations are produced by pipeline/translate_static.py (Haiku) and
// committed as src/data/guides.{lang}.json / glossary.{lang}.json.
// Slugs are identical across languages; only display fields are translated.
import gEN from '../data/guides.json';
import gES from '../data/guides.es.json';
import gPT from '../data/guides.pt.json';
import gDE from '../data/guides.de.json';
import gFR from '../data/guides.fr.json';
import gSW from '../data/guides.sw.json';
import gHA from '../data/guides.ha.json';
import gYO from '../data/guides.yo.json';
import gIG from '../data/guides.ig.json';
import gAM from '../data/guides.am.json';
import glEN from '../data/glossary.json';
import glES from '../data/glossary.es.json';
import glPT from '../data/glossary.pt.json';
import glDE from '../data/glossary.de.json';
import glFR from '../data/glossary.fr.json';
import glSW from '../data/glossary.sw.json';
import glHA from '../data/glossary.ha.json';
import glYO from '../data/glossary.yo.json';
import glIG from '../data/glossary.ig.json';
import glAM from '../data/glossary.am.json';

// English is the source of truth for WHICH entries exist; a translation file
// only supplies display text. Adding a guide and building before running the
// translator used to crash the [lang] route (it builds every slug for every
// language and found nothing to render), so entries missing from a translation
// fall back to their English text instead. The page still ships, in English,
// and picks up the translation on the next translator run.
function merge(source, translated, key) {
  if (!translated) return source;
  const byKey = new Map(translated.map((x) => [x[key], x]));
  return source.map((x) => byKey.get(x[key]) ?? x);
}

const G = {
  en: gEN.guides,
  es: merge(gEN.guides, gES.guides, 'slug'),
  pt: merge(gEN.guides, gPT.guides, 'slug'),
  de: merge(gEN.guides, gDE.guides, 'slug'),
  fr: merge(gEN.guides, gFR.guides, 'slug'),
  sw: merge(gEN.guides, gSW.guides, 'slug'),
  ha: merge(gEN.guides, gHA.guides, 'slug'),
  yo: merge(gEN.guides, gYO.guides, 'slug'),
  ig: merge(gEN.guides, gIG.guides, 'slug'),
  am: merge(gEN.guides, gAM.guides, 'slug'),
};
const GL = {
  en: glEN.terms,
  es: merge(glEN.terms, glES.terms, 'slug'),
  pt: merge(glEN.terms, glPT.terms, 'slug'),
  de: merge(glEN.terms, glDE.terms, 'slug'),
  fr: merge(glEN.terms, glFR.terms, 'slug'),
  sw: merge(glEN.terms, glSW.terms, 'slug'),
  ha: merge(glEN.terms, glHA.terms, 'slug'),
  yo: merge(glEN.terms, glYO.terms, 'slug'),
  ig: merge(glEN.terms, glIG.terms, 'slug'),
  am: merge(glEN.terms, glAM.terms, 'slug'),
};

// Date the editor-written source last changed (translations follow it).
// Keep in sync with CONTENT_UPDATED in astro.config.mjs.
export const contentUpdated = gEN.updated;
export const guidesFor = (lang) => G[lang] ?? G.en;
export const glossaryFor = (lang) => GL[lang] ?? GL.en;
export const glossarySetName = glEN.set;
