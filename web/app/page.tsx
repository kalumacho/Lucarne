import {
  loadConsultations,
  urgency,
  joursLabel,
  formatDate,
  sourceLabel,
} from "./lib/consultations";
import styles from "./page.module.css";

export default function Home() {
  const consultations = loadConsultations();
  const critiques = consultations.filter(
    (c) => c.days_left !== null && c.days_left <= 3,
  ).length;

  return (
    <main className={styles.main}>
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

      <ol className={styles.list}>
        {consultations.map((c) => {
          const u = urgency(c.days_left);
          return (
            <li key={c.url} className={`${styles.card} ${styles[u]}`}>
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
        })}
      </ol>

      <footer className={styles.pageFooter}>
        Données 100&nbsp;% publiques · Lucarne décrit, ne milite jamais · les
        dates incertaines sont signalées, jamais devinées.
      </footer>
    </main>
  );
}
