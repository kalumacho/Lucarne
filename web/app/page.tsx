import {
  loadConsultations,
  urgency,
  joursLabel,
  formatDate,
  sourceLabel,
  type Consultation,
} from "./lib/consultations";
import { departementName } from "./lib/departements";
import { createClient } from "./lib/supabase/server";
import styles from "./page.module.css";

function Card({ c }: { c: Consultation }) {
  const u = urgency(c.days_left);
  return (
    <li className={`${styles.card} ${styles[u]}`}>
      <div className={styles.meta}>
        <span className={`${styles.badge} ${styles[`badge_${u}`]}`}>
          {joursLabel(c.days_left)}
        </span>
        {sourceLabel(c.source) && (
          <span className={styles.source}>{sourceLabel(c.source)}</span>
        )}
        <span className={styles.contrib}>
          {c.contributions} contribution{c.contributions > 1 ? "s" : ""}
        </span>
      </div>

      <h2 className={styles.cardTitle}>{c.title}</h2>
      <p className={styles.digest}>{c.digest}</p>

      {c.departements.length > 0 && (
        <p className={styles.geo}>
          📍{" "}
          {c.departements
            .map((d) => departementName(d) ?? d)
            .join(" · ")}
        </p>
      )}

      <div className={styles.footer}>
        <span className={styles.dates}>
          Ouverte le {formatDate(c.opened_at)} · clôture le{" "}
          {formatDate(c.closes_at)}
        </span>
        <a
          className={styles.action}
          href={c.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          Participer →
        </a>
      </div>
    </li>
  );
}

export default async function Home() {
  const consultations = loadConsultations();
  const critiques = consultations.filter(
    (c) => c.days_left !== null && c.days_left <= 3,
  ).length;

  // Localisation de l'utilisateur connecté (profil Supabase).
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  let dept: string | null = null;
  if (user) {
    const { data } = await supabase
      .from("profiles")
      .select("departement")
      .eq("id", user.id)
      .maybeSingle();
    dept = data?.departement ?? null;
  }
  const near = dept
    ? consultations.filter((c) => c.departements.includes(dept!))
    : [];

  return (
    <main className={styles.main}>
      <nav className={styles.nav}>
        {user ? (
          <a href="/compte">Ma commune</a>
        ) : (
          <a href="/login">Créer mon radar local</a>
        )}
      </nav>

      <header className={styles.hero}>
        <div className={styles.kicker}>LUCARNE · POC</div>
        <h1 className={styles.title}>
          Ce qui se décide, <span>pendant qu’il est encore temps d’agir.</span>
        </h1>
        <p className={styles.sub}>
          Consultations publiques de l’État ouvertes, triées par urgence.
          Sources&nbsp;: portails officiels transition écologique, agriculture
          et économie.
        </p>
        <div className={styles.stats}>
          <span>
            <strong>{consultations.length}</strong> fenêtres ouvertes
          </span>
          <span className={styles.statAlert}>
            <strong>{critiques}</strong> ferment sous 72&nbsp;h
          </span>
        </div>
      </header>

      {dept && (
        <section className={styles.nearSection}>
          <h2 className={styles.sectionTitle}>
            Près de chez vous · {departementName(dept) ?? dept}
          </h2>
          {near.length > 0 ? (
            <ol className={styles.list}>
              {near.map((c) => (
                <Card key={c.url} c={c} />
              ))}
            </ol>
          ) : (
            <p className={styles.empty}>
              Aucune consultation ne cible spécifiquement votre département en
              ce moment. Les consultations nationales ci-dessous vous concernent
              aussi.
            </p>
          )}
        </section>
      )}

      <h2 className={styles.sectionTitle}>
        {dept ? "Toutes les consultations ouvertes" : ""}
      </h2>
      <ol className={styles.list}>
        {consultations.map((c) => (
          <Card key={c.url} c={c} />
        ))}
      </ol>

      <footer className={styles.pageFooter}>
        Données 100&nbsp;% publiques · Lucarne décrit, ne milite jamais · les
        dates incertaines sont signalées, jamais devinées.
      </footer>
    </main>
  );
}
