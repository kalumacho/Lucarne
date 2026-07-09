"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../lib/supabase/client";
import { cpToDepartement, departementName } from "../lib/departements";
import styles from "./compte.module.css";

type Props = {
  email: string;
  prenom: string;
  nom: string;
  ville: string;
  codePostal: string;
};

export default function ProfileForm({
  email,
  prenom,
  nom,
  ville,
  codePostal,
}: Props) {
  const router = useRouter();
  const [p, setP] = useState(prenom);
  const [n, setN] = useState(nom);
  const [v, setV] = useState(ville);
  const [cp, setCp] = useState(codePostal);
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">(
    "idle",
  );
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const dept = cpToDepartement(cp);
  const deptLabel = departementName(dept);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setState("saving");
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) {
      setState("error");
      return;
    }
    const { error } = await supabase.from("profiles").upsert({
      id: user.id,
      prenom: p.trim(),
      nom: n.trim(),
      ville: v.trim(),
      code_postal: cp.trim(),
      departement: dept,
      updated_at: new Date().toISOString(),
    });
    if (error) {
      setState("error");
    } else {
      setState("saved");
      router.refresh();
    }
  }

  async function logout() {
    await createClient().auth.signOut();
    router.push("/");
    router.refresh();
  }

  async function deleteAccount() {
    setDeleting(true);
    const supabase = createClient();
    const { error } = await supabase.rpc("delete_current_user");
    if (error) {
      setDeleting(false);
      setState("error");
      return;
    }
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <>
      <form className={styles.form} onSubmit={save}>
        <p className={styles.identity}>Connecté en tant que {email}</p>

        <div className={styles.row}>
          <label className={styles.label}>
            Prénom
            <input
              className={styles.input}
              type="text"
              placeholder="Sacha"
              value={p}
              onChange={(e) => setP(e.target.value)}
            />
          </label>
          <label className={styles.label}>
            Nom
            <input
              className={styles.input}
              type="text"
              placeholder="Cames"
              value={n}
              onChange={(e) => setN(e.target.value)}
            />
          </label>
        </div>

        <label className={styles.label}>
          Ville
          <input
            className={styles.input}
            type="text"
            required
            placeholder="Ex. Faremoutiers"
            value={v}
            onChange={(e) => setV(e.target.value)}
          />
        </label>

        <label className={styles.label}>
          Code postal
          <input
            className={styles.input}
            type="text"
            inputMode="numeric"
            required
            pattern="\d{4,5}"
            placeholder="Ex. 77515"
            value={cp}
            onChange={(e) => setCp(e.target.value)}
          />
        </label>

        {deptLabel && (
          <p className={styles.hint}>
            Département détecté&nbsp;: <strong>{deptLabel}</strong> ({dept})
          </p>
        )}

        <button
          className={styles.button}
          type="submit"
          disabled={state === "saving"}
        >
          {state === "saving" ? "Enregistrement…" : "Enregistrer"}
        </button>

        {state === "saved" && (
          <p className={styles.success}>
            Enregistré. <a href="/">Voir mes consultations locales →</a>
          </p>
        )}
        {state === "error" && (
          <p className={styles.error}>Une erreur est survenue. Réessayez.</p>
        )}
      </form>

      <div className={styles.account}>
        <p className={styles.accountTitle}>Gestion du compte</p>

        <button type="button" className={styles.logout} onClick={logout}>
          Se déconnecter
        </button>

        {confirmDelete ? (
          <div className={styles.dangerBox}>
            <p>
              Cette action est définitive : votre compte et vos informations
              seront supprimés, sans possibilité de retour.
            </p>
            <div className={styles.dangerActions}>
              <button
                type="button"
                className={styles.confirmDelete}
                onClick={deleteAccount}
                disabled={deleting}
              >
                {deleting ? "Suppression…" : "Supprimer définitivement"}
              </button>
              <button
                type="button"
                className={styles.cancel}
                onClick={() => setConfirmDelete(false)}
                disabled={deleting}
              >
                Annuler
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            className={styles.danger}
            onClick={() => setConfirmDelete(true)}
          >
            Supprimer mon compte
          </button>
        )}
      </div>
    </>
  );
}
