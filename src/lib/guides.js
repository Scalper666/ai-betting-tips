// Localized datasets for editor-written static content (guides + glossary).
// Translations are produced by pipeline/translate_static.py (Haiku) and
// committed as src/data/guides.{lang}.json / glossary.{lang}.json.
// Slugs are identical across languages; only display fields are translated.
import gEN from '../data/guides.json';
import gES from '../data/guides.es.json';
import gPT from '../data/guides.pt.json';
import gDE from '../data/guides.de.json';
import gFR from '../data/guides.fr.json';
import glEN from '../data/glossary.json';
import glES from '../data/glossary.es.json';
import glPT from '../data/glossary.pt.json';
import glDE from '../data/glossary.de.json';
import glFR from '../data/glossary.fr.json';

const G = { en: gEN.guides, es: gES.guides, pt: gPT.guides, de: gDE.guides, fr: gFR.guides };
const GL = { en: glEN.terms, es: glES.terms, pt: glPT.terms, de: glDE.terms, fr: glFR.terms };

// Date the editor-written source last changed (translations follow it).
// Keep in sync with CONTENT_UPDATED in astro.config.mjs.
export const contentUpdated = gEN.updated;
export const guidesFor = (lang) => G[lang] ?? G.en;
export const glossaryFor = (lang) => GL[lang] ?? GL.en;
export const glossarySetName = glEN.set;
