import { redirect } from "next/navigation";
import { createClient } from "../lib/supabase/server";
import ProfileForm from "./ProfileForm";
import styles from "./compte.module.css";

export const dynamic = "force-dynamic";

export default async function Compte() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("profiles")
    .select("ville, code_postal")
    .eq("id", user.id)
    .maybeSingle();

  return (
    <main className={styles.wrap}>
      <a className={styles.back} href="/">
        ← Retour aux consultations
      </a>
      <h1 className={styles.title}>Ma commune</h1>
      <p className={styles.lead}>
        Indiquez votre ville et votre code postal. Lucarne mettra en avant les
        consultations qui concernent votre département.
      </p>
      <ProfileForm
        email={user.email ?? ""}
        ville={profile?.ville ?? ""}
        codePostal={profile?.code_postal ?? ""}
      />
    </main>
  );
}
