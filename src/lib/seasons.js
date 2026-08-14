// Localized season datasets. Translations come from pipeline/translate_static.py
// and live in src/data/seasons.{lang}.json; slugs are language-independent, so
// a season missing from a translation falls back to its English entry rather
// than breaking the [lang] route (same guard as lib/guides.js).
import sEN from '../data/seasons.json';
import sES from '../data/seasons.es.json';
import sPT from '../data/seasons.pt.json';
import sDE from '../data/seasons.de.json';
import sFR from '../data/seasons.fr.json';
import sSW from '../data/seasons.sw.json';
import sHA from '../data/seasons.ha.json';
import sYO from '../data/seasons.yo.json';
import sIG from '../data/seasons.ig.json';
import sAM from '../data/seasons.am.json';

function merge(source, translated) {
  if (!translated) return source;
  const byKey = new Map(translated.map((x) => [x.slug, x]));
  return source.map((x) => byKey.get(x.slug) ?? x);
}

const S = {
  en: sEN.seasons,
  es: merge(sEN.seasons, sES.seasons),
  pt: merge(sEN.seasons, sPT.seasons),
  de: merge(sEN.seasons, sDE.seasons),
  fr: merge(sEN.seasons, sFR.seasons),
  sw: merge(sEN.seasons, sSW.seasons),
  ha: merge(sEN.seasons, sHA.seasons),
  yo: merge(sEN.seasons, sYO.seasons),
  ig: merge(sEN.seasons, sIG.seasons),
  am: merge(sEN.seasons, sAM.seasons),
};

export const seasonsFor = (lang) => S[lang] ?? S.en;
export const seasonBySlug = (lang, slug) => seasonsFor(lang).find((s) => s.slug === slug) ?? null;
