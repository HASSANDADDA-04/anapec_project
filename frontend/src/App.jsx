import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, clearSession, currentUser, downloadFile, downloadPdf, setSession } from "./api";

const LEVELS = ["", "bac", "bac+2", "bac+3", "bac+5", "doctorat"];
const ROLE_LABEL = { candidate: "Candidat", entreprise: "Entreprise", admin: "Administrateur" };

function initials(name) {
  return (name || "A").split(" ").slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function Icon({ name }) {
  const paths = {
    user: "M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm-7 9v-1c0-2.8 2.6-5 7-5s7 2.2 7 5v1H5Z",
    brief: "M8 7V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h3Zm2 0h4V6h-4v1Z",
    file: "M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Zm7 1.5V9h4.5L14 4.5Z",
    plus: "M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6V5Z",
    board: "M4 4h7v7H4V4Zm9 0h7v4h-7V4ZM4 13h7v7H4v-7Zm9-3h7v10h-7V10Z",
    bell: "M12 3a6 6 0 0 0-6 6v3.2L4.3 15a1 1 0 0 0 .8 1.6h13.8a1 1 0 0 0 .8-1.6L18 12.2V9a6 6 0 0 0-6-6Zm0 18a2.4 2.4 0 0 0 2.3-2h-4.6A2.4 2.4 0 0 0 12 21Z",
    people: "M8 11a3 3 0 1 0-3-3 3 3 0 0 0 3 3Zm8-1a2.5 2.5 0 1 0-2.5-2.5A2.5 2.5 0 0 0 16 10ZM3.5 19v-1A4.5 4.5 0 0 1 8 13.5 4.5 4.5 0 0 1 12.5 18v1h-9Zm9.2 0v-1a5.4 5.4 0 0 0-1.2-3.3 4 4 0 0 1 2.5-.8 4.2 4.2 0 0 1 4.2 4.1v1h-5.5Z",
  };
  return (
    <svg className="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[name]} fill="currentColor" />
    </svg>
  );
}

function ScoreRing({ value }) {
  const number = Number(value);
  const angle = Number.isFinite(number) ? Math.max(0, Math.min(100, number)) * 3.6 : 0;
  return (
    <div className="ring" style={{ "--p": `${angle}deg` }}>
      <strong>{value ?? "—"}</strong>
      <span>sur 100</span>
    </div>
  );
}

function destination(user) {
  if (user.role === "admin") return "/admin";
  if (user.role === "entreprise") return "/offres";
  return "/profil";
}

const DOMAINS = [
  "Informatique",
  "Comptabilité et finance",
  "Commerce et vente",
  "Ressources humaines",
  "Communication",
  "Industrie",
  "Bâtiment",
  "Santé",
  "Enseignement",
  "Transport et logistique",
  "Hôtellerie et restauration",
  "Agriculture",
];

function Home() {
  const user = currentUser();
  return (
    <div className="home">
      <header className="home-bar">
        <Link to="/" className="home-brand">
          <span className="brand-mark">AN</span>
          <span>
            <strong>ANAPEC</strong>
            <small>Emploi public</small>
          </span>
        </Link>
        <nav className="home-nav">
          <a href="#espaces">Pour vous</a>
          <a href="#domaines">Métiers</a>
        </nav>
        <div className="home-actions">
          {user ? (
            <Link className="button" to={destination(user)}>Mon espace</Link>
          ) : (
            <>
              <Link className="button secondary" to="/connexion">Connexion</Link>
              <Link className="button" to="/registre">Créer un compte</Link>
            </>
          )}
        </div>
      </header>

      <section className="home-hero">
        <div className="home-wrap hero-grid">
          <div className="hero-copy">
            <div className="eyebrow">Agence nationale de promotion de l'emploi</div>
            <h1>Trouvez un emploi. Recrutez la bonne personne.</h1>
            <p className="home-lead">Des offres dans les villes du Maroc. Vous envoyez votre candidature, ou vous recevez celles des personnes intéressées par votre poste.</p>
            <div className="home-actions">
              <Link className="button gold" to="/registre">Créer un compte</Link>
              <Link className="button ghost" to="/connexion">Se connecter</Link>
            </div>
          </div>
          <div className="hero-services">
            <Link className="svc" to="/registre?role=candidate">
              <span className="svc-icon green">CV</span>
              <span>
                <small>Vous cherchez un emploi</small>
                <strong>Voir les offres</strong>
                <em>Choisissez un poste et envoyez votre candidature.</em>
              </span>
            </Link>
            <Link className="svc" to="/registre?role=entreprise">
              <span className="svc-icon navy">RH</span>
              <span>
                <small>Vous recrutez</small>
                <strong>Publier une offre</strong>
                <em>Recevez les candidatures et répondez à chacune.</em>
              </span>
            </Link>
          </div>
        </div>
      </section>

      <section className="home-facts">
        <div className="home-wrap">
          <article><b>12</b><span>Métiers, de l'informatique à l'agriculture.</span></article>
          <article><b>Maroc</b><span>Des offres dans les villes du pays.</span></article>
          <article><b>Réponse</b><span>Vous savez où en est votre candidature.</span></article>
        </div>
      </section>

      <section className="home-section" id="espaces">
        <div className="home-wrap">
          <h2>Pour vous</h2>
          <div className="home-spaces">
            <article>
              <small>Candidat</small>
              <h3>Vous cherchez un emploi</h3>
              <p>Parcourez les offres, envoyez votre candidature et suivez la réponse de l'entreprise.</p>
              <Link to="/registre?role=candidate">Créer mon compte candidat</Link>
            </article>
            <article>
              <small>Entreprise</small>
              <h3>Vous avez un poste à pourvoir</h3>
              <p>Publiez votre offre, lisez les candidatures et dites si la personne est retenue.</p>
              <Link to="/registre?role=entreprise">Créer mon compte entreprise</Link>
            </article>
          </div>
        </div>
      </section>

      <section className="home-section alt" id="domaines">
        <div className="home-wrap">
          <h2>Les métiers</h2>
          <p className="home-lead dark">Informatique, commerce, santé, hôtellerie, agriculture et les autres métiers du pays.</p>
          <ul className="domain-grid">
            {DOMAINS.map((name, index) => (
              <li key={name}><small>{String(index + 1).padStart(2, "0")}</small><span>{name}</span></li>
            ))}
          </ul>
        </div>
      </section>

      <section className="home-close">
        <div className="home-wrap">
          <h2>Commencez aujourd'hui.</h2>
          <p>Un compte suffit pour chercher un emploi ou pour recruter.</p>
          <div className="home-actions">
            <Link className="button gold" to="/registre?role=candidate">Je cherche un emploi</Link>
            <Link className="button ghost" to="/registre?role=entreprise">Je recrute</Link>
          </div>
        </div>
      </section>

      <footer className="home-foot">
        <strong>ANAPEC</strong>
        <span>Emploi public</span>
      </footer>
    </div>
  );
}

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const data = await api("/auth/login", { method: "POST", body: { email, password } });
      setSession(data.token, data.user);
      navigate(destination(data.user));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="auth-page">
      <header className="auth-bar">
        <Link to="/" className="home-brand">
          <span className="brand-mark">AN</span>
          <span><strong>ANAPEC</strong><small>Emploi public</small></span>
        </Link>
        <Link className="button secondary" to="/">Accueil</Link>
      </header>
      <main className="auth-main">
        <form className="card login-card" onSubmit={submit}>
          <div className="eyebrow">Espace privé</div>
          <h2>Connexion</h2>
          <p className="form-note">E-mail et mot de passe du compte.</p>
          <label>E-mail</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
          <label>Mot de passe</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
          {error && <p className="error">{error}</p>}
          <button className="wide" type="submit">Se connecter</button>
          <p className="switch-auth">Pas encore de compte ? <Link to="/registre">Créer un compte</Link></p>
        </form>
      </main>
    </div>
  );
}

function Register() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [role, setRole] = useState(params.get("role") === "entreprise" ? "entreprise" : "candidate");
  const [lastName, setLastName] = useState("");
  const [firstName, setFirstName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [domains, setDomains] = useState([]);
  const [domainId, setDomainId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { api("/domains").then(setDomains).catch(() => {}); }, []);

  async function submit(event) {
    event.preventDefault();
    setError("");
    if (password !== passwordConfirm) {
      setError("Les deux mots de passe ne correspondent pas.");
      return;
    }
    const fullName = role === "candidate"
      ? `${firstName.trim()} ${lastName.trim()}`.trim()
      : companyName.trim();
    try {
      const data = await api("/auth/register", {
        method: "POST",
        body: {
          full_name: fullName,
          email,
          password,
          password_confirm: passwordConfirm,
          role,
          birth_date: role === "candidate" ? birthDate : "",
          domain_id: role === "entreprise" ? Number(domainId) : null,
        },
      });
      setSession(data.token, data.user);
      navigate(destination(data.user));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="auth-page">
      <header className="auth-bar">
        <Link to="/" className="home-brand">
          <span className="brand-mark">AN</span>
          <span><strong>ANAPEC</strong><small>Emploi public</small></span>
        </Link>
        <Link className="button secondary" to="/">Accueil</Link>
      </header>
      <main className="auth-main">
        <form className="card login-card register-card" onSubmit={submit}>
          <div className="eyebrow">Inscription</div>
          <h2>Créer un compte</h2>
          <label>Je suis</label>
          <div className="role-choice">
            <button type="button" className={role === "candidate" ? "active" : ""} onClick={() => setRole("candidate")}><b>Candidat</b><small>Déposer un CV</small></button>
            <button type="button" className={role === "entreprise" ? "active" : ""} onClick={() => setRole("entreprise")}><b>Entreprise</b><small>Publier une offre</small></button>
          </div>
          {role === "candidate" ? (
            <>
              <div className="field-row">
                <div>
                  <label>Nom</label>
                  <input value={lastName} onChange={(e) => setLastName(e.target.value)} required />
                </div>
                <div>
                  <label>Prénom</label>
                  <input value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
                </div>
              </div>
              <label>Date de naissance</label>
              <input type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} required />
            </>
          ) : (
            <>
              <label>Nom de l'entreprise</label>
              <input value={companyName} onChange={(e) => setCompanyName(e.target.value)} required />
              <label>Domaine</label>
              <select value={domainId} onChange={(e) => setDomainId(e.target.value)} required>
                <option value="">Choisir</option>
                {domains.map((domain) => <option key={domain.id} value={domain.id}>{domain.name}</option>)}
              </select>
            </>
          )}
          <label>E-mail</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
          <div className="field-row">
            <div>
              <label>Mot de passe</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} autoComplete="new-password" />
            </div>
            <div>
              <label>Confirmer le mot de passe</label>
              <input type="password" value={passwordConfirm} onChange={(e) => setPasswordConfirm(e.target.value)} required minLength={6} autoComplete="new-password" />
            </div>
          </div>
          {error && <p className="error">{error}</p>}
          <button className="wide" type="submit">Créer le compte</button>
          <p className="switch-auth">Déjà inscrit ? <Link to="/connexion">Se connecter</Link></p>
        </form>
      </main>
    </div>
  );
}

function Notices() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const data = await api("/notices");
        if (alive) setRows(data);
      } catch {
        if (alive) setRows([]);
      }
    }
    load();
    const timer = setInterval(load, 8000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  async function dismiss(id) {
    setRows((current) => current.filter((row) => row.id !== id));
    try {
      await api(`/notices/${id}/read`, { method: "POST" });
    } catch {
      /* Le message reste visible au prochain chargement s'il n'a pas été lu. */
    }
  }

  if (rows.length === 0) return null;
  return (
    <div className="notice-stack">
      {rows.map((row) => (
        <section className={`card notice ${row.kind === "acceptee" ? "ok" : "bad"}`} key={row.id}>
          <p>{row.message}</p>
          <div className="actions">
            <Link className="button" to="/candidatures" onClick={() => dismiss(row.id)}>Voir ma candidature</Link>
            <button type="button" className="secondary" onClick={() => dismiss(row.id)}>J'ai vu</button>
          </div>
        </section>
      ))}
    </div>
  );
}

function Shell({ children }) {
  const navigate = useNavigate();
  const user = currentUser();
  if (!user) return <Navigate to="/connexion" replace />;
  const links = user.role === "admin"
    ? [["/admin", "Tableau de bord", "board"], ["/admin/gestion", "Comptes", "people"], ["/admin/alertes", "Alertes", "bell"], ["/offres", "Offres", "brief"]]
    : user.role === "entreprise"
      ? [["/offres", "Mes offres", "brief"], ["/offres/nouvelle", "Publier une offre", "plus"]]
      : [["/profil", "Mon profil", "user"], ["/offres", "Offres", "brief"], ["/candidatures", "Mes candidatures", "file"]];

  return (
    <div className={`shell role-${user.role}`}>
      <aside className="side">
        <div className="brand">
          <span className="brand-mark">AN</span>
          <div>
            <strong>ANAPEC</strong>
            <small>{ROLE_LABEL[user.role] || "Espace"}</small>
          </div>
        </div>
        <nav>
          {links.map(([to, label, icon]) => (
            <NavLink key={to} to={to} end className={({ isActive }) => (isActive ? "active" : "")}><Icon name={icon} />{label}</NavLink>
          ))}
        </nav>
        <div className="spacer" />
        <div className="who">
          <span className="avatar">{initials(user.full_name)}</span>
          <div>
            <strong>{user.full_name}</strong>
            <small>{ROLE_LABEL[user.role] || user.role}</small>
          </div>
        </div>
        <button className="link" onClick={() => { clearSession(); navigate("/"); }}>Quitter</button>
      </aside>
      <main className="content">
        {user.role === "candidate" && <Notices />}
        {children}
      </main>
    </div>
  );
}

function Profile() {
  const [profile, setProfile] = useState(null);
  const [domains, setDomains] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [phase, setPhase] = useState(-1);
  const [ready, setReady] = useState(false);
  const [marks, setMarks] = useState({});
  const analysisRun = useRef(null);
  const cvPhases = [
    { title: "Lecture du CV", detail: "Le fichier déposé est relu, phrase par phrase." },
    { title: "Compétences", detail: "Les compétences écrites dans le CV sont relevées.", key: "skills" },
    { title: "Langues", detail: "Les langues écrites dans le CV sont relevées.", key: "languages" },
    { title: "Stages", detail: "Les périodes de stage datées sont additionnées.", key: "experience" },
    { title: "Diplôme", detail: "Un diplôme compte seulement s'il est obtenu.", key: "diploma" },
    { title: "Parcours", detail: "Les formations écrites dans le CV sont relevées.", key: "studies" },
    { title: "Domaine", detail: "Le domaine choisi est comparé à ce qui est écrit dans le CV.", key: "domain" },
  ];

  useEffect(() => {
    api("/profile").then(setProfile).catch((err) => setError(err.message));
    api("/domains").then(setDomains).catch(() => {});
  }, []);

  if (!profile) return <Shell><p>{error || "Chargement..."}</p></Shell>;

  function update(field, value) {
    setProfile({ ...profile, [field]: value });
  }

  async function save(event) {
    event.preventDefault();
    setError("");
    try {
      const result = await api("/profile", {
        method: "PUT",
        body: {
          domain_id: Number(profile.domain_id) || null,
          city: profile.city,
          phone: profile.phone,
          birth_date: profile.birth_date || "",
        },
      });
      setProfile({ ...profile, coherence: result.coherence, coherence_note: result.coherence_note });
      setMessage("Profil enregistré.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function upload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError("");
    const body = new FormData();
    body.append("file", file);
    try {
      const result = await api("/cv", { method: "POST", body });
      setProfile({
        ...profile,
        cv_filename: result.filename,
        cv_text: result.text,
        coherence: result.coherence,
        coherence_note: result.coherence_note,
      });
      setCvAnalysis(null);
      setPhase(-1);
      setReady(false);
      setMarks({});
      setMessage("CV enregistré. Vous pouvez maintenant l'analyser.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function analyzeCv() {
    setError("");
    setMessage("");
    if (!profile.cv_filename) {
      setError("Déposez un CV avant de l'analyser.");
      return;
    }
    if (!profile.domain_id) {
      setError("Choisissez un domaine avant d'analyser le CV.");
      return;
    }
    const run = { stopped: false, controller: new AbortController(), cancelWait: null };
    analysisRun.current = run;
    setAnalyzing(true);
    setReady(false);
    setCvAnalysis(null);
    setMarks({});
    setPhase(0);
    const pending = api("/profile/analyze", {
      method: "POST",
      body: { domain_id: Number(profile.domain_id) },
      signal: run.controller.signal,
    });
    const wait = (ms) => new Promise((resolve, reject) => {
      if (run.stopped) {
        reject(new DOMException("Analyse arrêtée", "AbortError"));
        return;
      }
      const timer = setTimeout(() => {
        run.cancelWait = null;
        if (run.stopped) reject(new DOMException("Analyse arrêtée", "AbortError"));
        else resolve();
      }, ms);
      run.cancelWait = () => {
        clearTimeout(timer);
        reject(new DOMException("Analyse arrêtée", "AbortError"));
      };
    });
    try {
      let result = null;
      for (let index = 0; index < cvPhases.length; index += 1) {
        if (run.stopped) throw new DOMException("Analyse arrêtée", "AbortError");
        setPhase(index);
        if (cvPhases[index].key === "skills") {
          result = await pending;
          if (run.stopped) throw new DOMException("Analyse arrêtée", "AbortError");
          setCvAnalysis(result);
          setProfile({ ...profile, domain_id: Number(profile.domain_id), coherence: result.coherence, coherence_note: result.coherence_note });
        }
        await wait(1600);
        if (run.stopped) throw new DOMException("Analyse arrêtée", "AbortError");
        if (cvPhases[index].key) setMarks((current) => ({ ...current, [cvPhases[index].key]: true }));
      }
      setReady(true);
    } catch (err) {
      if (err.name === "AbortError") {
        setPhase(-1);
        setReady(false);
        setCvAnalysis(null);
        setMarks({});
      } else {
        setError(err.message);
        setPhase(-1);
      }
    } finally {
      analysisRun.current = null;
      setAnalyzing(false);
    }
  }

  function stopAnalysis() {
    const run = analysisRun.current;
    if (!run) return;
    run.stopped = true;
    run.controller.abort();
    run.cancelWait?.();
  }

  const tag = profile.coherence === "coherent" ? "ok" : profile.coherence === "incoherent" ? "bad" : "warn";

  return (
    <Shell>
      <div className="page-head">
        <div>
          <div className="eyebrow">Candidat</div>
          <h1>Mon profil</h1>
          <p>Le diplôme, l'expérience et les langues sont lus dans le CV.</p>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      {message && <p className="ok-note">{message}</p>}
      <div className="row">
        <form className="card" onSubmit={save}>
          <label>Domaine</label>
          <select value={profile.domain_id || ""} onChange={(e) => update("domain_id", e.target.value)}>
            <option value="">Choisir</option>
            {domains.map((domain) => <option key={domain.id} value={domain.id}>{domain.name}</option>)}
          </select>
          <label>Date de naissance</label>
          <input type="date" value={profile.birth_date || ""} onChange={(e) => update("birth_date", e.target.value)} />
          <label>Ville</label>
          <input value={profile.city || ""} onChange={(e) => update("city", e.target.value)} />
          <label>Téléphone</label>
          <input value={profile.phone || ""} onChange={(e) => update("phone", e.target.value)} />
          <button className="wide" type="submit">Enregistrer</button>
        </form>
        <section className="card">
          <h2>CV</h2>
          <label className="file">
            Choisissez un PDF ou un Word enregistré sur votre ordinateur.
            <input type="file" accept=".pdf,.docx" onChange={upload} />
          </label>
          {profile.cv_filename && <p>Fichier : {profile.cv_filename}</p>}
          <div className="actions">
            <button type="button" onClick={analyzeCv} disabled={analyzing || !profile.cv_filename}>
              {analyzing ? "Analyse..." : "Analyser mon CV"}
            </button>
            {analyzing && <button type="button" className="danger" onClick={stopAnalysis}>Arrêter l'analyse</button>}
          </div>
          {!profile.cv_filename && <p className="muted">Déposez un CV pour pouvoir l'analyser.</p>}
          {phase < 0 && profile.coherence && <p><span className={`tag ${tag}`}>{profile.coherence}</span> {profile.coherence_note}</p>}
          {phase < 0 && profile.coherence === "incoherent" && <p className="error">Tant que le domaine ne correspond pas au CV, vous ne pouvez pas postuler.</p>}
          {phase >= 0 && (
            <div className="analysis-board">
              <div className="analysis-head">
                <div>
                  <div className="eyebrow">{ready ? "Lecture terminée" : "Lecture en cours"}</div>
                  <h2>Ce que contient le CV</h2>
                </div>
                <strong>{ready ? 100 : Math.round(((phase + 0.4) / cvPhases.length) * 100)}%</strong>
              </div>
              <div className="meter" aria-hidden="true"><span style={{ width: `${ready ? 100 : ((phase + 0.4) / cvPhases.length) * 100}%` }} /></div>
              <p className="phase-note">{cvPhases[Math.min(phase, cvPhases.length - 1)].detail}</p>
              <ol className="calc-steps profile-steps">
                {cvPhases.map((item, index) => (
                  <li key={item.title} className={index < phase || (ready && index === phase) ? "done" : index === phase ? "current" : ""}>
                    <span>{index < phase || ready ? "✓" : index === phase ? "…" : index + 1}</span>
                    <div>
                      <strong>{item.title}</strong>
                      <small>{index < phase || ready ? "Terminé" : index === phase ? "En cours" : "En attente"}</small>
                    </div>
                  </li>
                ))}
              </ol>
              {cvAnalysis && marks.skills && (
                <div className="cv-finding">
                  <h3>Compétences écrites dans le CV</h3>
                  {cvAnalysis.skills.length === 0 && <p className="muted">Aucune compétence lisible dans le fichier.</p>}
                  <p>{cvAnalysis.skills.map((skill) => <span className="tag" key={skill}>{skill}</span>)}</p>
                </div>
              )}
              {cvAnalysis && marks.languages && (
                <p className="cv-finding"><strong>Langues :</strong> {cvAnalysis.languages || "aucune lue"}</p>
              )}
              {cvAnalysis && marks.experience && (
                <p className="cv-finding"><strong>Stages :</strong> {cvAnalysis.experience_months ? `${cvAnalysis.experience_months} mois` : "aucun lu"}</p>
              )}
              {cvAnalysis && marks.diploma && (
                <p className="cv-finding"><strong>Diplôme obtenu :</strong> {cvAnalysis.diploma || "aucun"}</p>
              )}
              {cvAnalysis && marks.studies && (
                <div className="cv-finding">
                  <h3>Parcours lu dans le CV</h3>
                  {cvAnalysis.studies.length === 0 && <p className="muted">Aucune formation nommée dans le fichier.</p>}
                  {cvAnalysis.studies.map((line) => <p key={line}>{line}</p>)}
                </div>
              )}
              {cvAnalysis && marks.domain && (
                <div className="cv-finding">
                  <p><span className={`tag ${tag}`}>{cvAnalysis.coherence}</span> {cvAnalysis.coherence_note}</p>
                  {cvAnalysis.coherence === "incoherent" && <p className="error">Tant que le domaine ne correspond pas au CV, vous ne pouvez pas postuler.</p>}
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </Shell>
  );
}

function Offers() {
  const user = currentUser();
  const [offers, setOffers] = useState([]);
  const [error, setError] = useState("");
  const [coherence, setCoherence] = useState("");
  const [coherenceNote, setCoherenceNote] = useState("");
  const [domains, setDomains] = useState([]);
  const [filters, setFilters] = useState({ q: "", city: "", domain_id: "" });
  const blocked = user?.role === "candidate" && coherence === "incoherent";
  function load(next = filters) {
    const params = new URLSearchParams();
    if (next.q.trim()) params.set("q", next.q.trim());
    if (next.city) params.set("city", next.city);
    if (next.domain_id) params.set("domain_id", next.domain_id);
    const query = params.toString();
    api(query ? `/offers?${query}` : "/offers").then(setOffers).catch((err) => setError(err.message));
  }
  useEffect(() => { load({ q: "", city: "", domain_id: "" }); api("/domains").then(setDomains).catch(() => {}); }, []);
  useEffect(() => {
    if (user?.role !== "candidate") return;
    api("/profile").then((profile) => {
      setCoherence(profile.coherence || "");
      setCoherenceNote(profile.coherence_note || "");
    }).catch(() => {});
  }, [user?.role]);
  async function toggle(offer) {
    await api(`/offers/${offer.id}`, { method: "PATCH", body: { is_active: offer.status !== "online" } });
    load();
  }
  return (
    <Shell>
      <div className="page-head">
        <div>
          <div className="eyebrow">Marché</div>
          <h1>Offres</h1>
          <p>{user?.role === "candidate" ? "Les offres ouvertes. Choisissez un poste et envoyez votre candidature." : user?.role === "admin" ? "Les offres publiées par les entreprises." : "Vos offres, et les personnes qui ont postulé."}</p>
        </div>
        {user?.role === "entreprise" && <Link className="button" to="/offres/nouvelle">Publier</Link>}
      </div>
      {user?.role === "candidate" && (
        <form className="filters" onSubmit={(event) => { event.preventDefault(); load(); }}>
          <div>
            <label>Mot</label>
            <input value={filters.q} placeholder="Poste ou compétence" onChange={(event) => setFilters({ ...filters, q: event.target.value })} />
          </div>
          <div>
            <label>Ville</label>
            <select value={filters.city} onChange={(event) => setFilters({ ...filters, city: event.target.value })}>
              <option value="">Toutes les villes</option>
              {MOROCCO_CITIES.map((city) => <option key={city} value={city}>{city}</option>)}
            </select>
          </div>
          <div>
            <label>Métier</label>
            <select value={filters.domain_id} onChange={(event) => setFilters({ ...filters, domain_id: event.target.value })}>
              <option value="">Tous les métiers</option>
              {domains.map((domain) => <option key={domain.id} value={domain.id}>{domain.name}</option>)}
            </select>
          </div>
          <button type="submit">Chercher</button>
        </form>
      )}
      {error && <p className="error">{error}</p>}
      {blocked && (
        <section className="card">
          <p>Votre domaine ne correspond pas à votre CV. Vous ne pouvez pas postuler.</p>
          {coherenceNote && <p>{coherenceNote}</p>}
          <Link className="button" to="/profil">Corriger Mon profil</Link>
        </section>
      )}
      <div className="list">
        {offers.map((offer) => (
          <article className="card offer-card job" key={offer.id}>
            <div className="job-body">
              <div className="job-kicker">
                <span className="tag">{offer.domain_name}</span>
                <span className={`tag ${offer.status === "online" ? "ok" : "warn"}`}>{offer.status === "online" ? "En ligne" : "Retirée"}</span>
              </div>
              <h2>{offer.title}</h2>
              <p className="meta">{offer.city} · {offer.diploma_level || "diplôme non précisé"} · {offer.years_required} an(s) d'expérience</p>
              <p className="offer-copy">{offer.description}</p>
              <p className="offer-skills">{offer.skills.map((skill) => <span className="tag" key={skill.id}>{skill.label}</span>)}</p>
            </div>
            <div className="job-side">
              {user?.role === "candidate" && offer.status === "online" && !offer.applied && !blocked && <Link className="button" to={`/offres/${offer.id}`}>Analyser et postuler</Link>}
              {user?.role === "candidate" && offer.applied && <Link className="button secondary" to="/candidatures">Déjà postulé</Link>}
              {user?.role !== "candidate" && <Link className="button secondary" to={`/offres/${offer.id}/candidatures`}>Candidatures</Link>}
              {user?.role === "entreprise" && <Link className="button secondary" to={`/offres/${offer.id}/modifier`}>Modifier</Link>}
              {user?.role === "entreprise" && <button className="secondary" onClick={() => toggle(offer)}>{offer.status === "online" ? "Retirer" : "Remettre en ligne"}</button>}
            </div>
          </article>
        ))}
        {offers.length === 0 && <p className="empty">Aucune offre ne correspond.</p>}
      </div>
    </Shell>
  );
}

const MOROCCO_CITIES = [
  "Agadir", "Aïn Harrouda", "Aït Baha", "Aït Melloul", "Aït Ourir", "Al Hoceïma", "Asilah", "Assa",
  "Azemmour", "Azilal", "Azrou", "Ben Guerir", "Béni Mellal", "Benslimane", "Berkane", "Berrechid",
  "Biougra", "Bouarfa", "Boujdour", "Boulemane", "Bouskoura", "Bouznika", "Casablanca", "Chefchaouen",
  "Chichaoua", "Dakhla", "Dcheira El Jihadia", "Demnate", "Driouch", "El Hajeb", "El Jadida",
  "El Kelaa des Sraghna", "Errachidia", "Essaouira", "Fès", "Figuig", "Fnideq", "Fquih Ben Salah",
  "Guelmim", "Guercif", "Ifrane", "Imzouren", "Inezgane", "Jerada", "Kénitra", "Khémisset", "Khénifra",
  "Khouribga", "Ksar El Kébir", "Ksar Sghir", "Laâyoune", "Larache", "Marrakech", "Martil", "Médiouna",
  "Mehdia", "Meknès", "Midelt", "Missour", "Mohammedia", "Moulay Yacoub", "Nador", "Nouaceur",
  "Ouarzazate", "Oued Zem", "Oujda", "Oulad Teima", "Ouazzane", "Rabat", "Rommani", "Safi", "Saïdia",
  "Salé", "Sefrou", "Selouane", "Settat", "Sidi Bennour", "Sidi Ifni", "Sidi Kacem", "Sidi Slimane",
  "Skhirate", "Smara", "Souk El Arbaa", "Tahannaout", "Tan-Tan", "Tanger", "Taounate", "Taourirt",
  "Tarfaya", "Taroudant", "Tata", "Taza", "Témara", "Tétouan", "Tiflet", "Tinghir", "Tiznit",
  "Youssoufia", "Zagora",
].sort((a, b) => a.localeCompare(b, "fr"));

const OFFER_LANGUAGES = [
  "Français", "Anglais", "Arabe", "Amazigh", "Espagnol", "Allemand", "Italien", "Portugais",
  "Néerlandais", "Chinois", "Japonais", "Russe", "Turc", "Hindi", "Coréen", "Suédois",
];

function NewOffer({ editing = false }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const [company, setCompany] = useState(null);
  const [skills, setSkills] = useState([]);
  const [chosen, setChosen] = useState([]);
  const [query, setQuery] = useState("");
  const [languages, setLanguages] = useState(["Français"]);
  const [form, setForm] = useState({ title: "", city: "Casablanca", description: "", diploma_level: "bac+2", years_required: 1 });
  const [error, setError] = useState("");

  useEffect(() => {
    api("/auth/me").then(async (me) => {
      setCompany(me);
      if (editing) {
        const rows = await api("/offers");
        const offer = rows.find((row) => String(row.id) === id);
        if (!offer) {
          setError("Offre introuvable");
          return;
        }
        setForm({
          title: offer.title,
          city: offer.city || "Casablanca",
          description: offer.description || "",
          diploma_level: offer.diploma_level || "",
          years_required: offer.years_required || 0,
        });
        setChosen(offer.skills.map((skill) => ({ id: skill.id, label: skill.label })));
        setLanguages((offer.languages || "").split(",").map((item) => item.trim()).filter(Boolean));
      }
      if (me.domain_id) searchSkills("", me.domain_id);
    }).catch((err) => setError(err.message));
  }, [editing, id]);

  async function searchSkills(value, domainId = company?.domain_id) {
    setQuery(value);
    if (!domainId) {
      setSkills([]);
      return;
    }
    const params = new URLSearchParams();
    if (value) params.set("q", value);
    params.set("domain_id", domainId);
    const rows = await api(`/skills?${params.toString()}`);
    setSkills(rows);
  }

  function toggleLanguage(name) {
    setLanguages((current) => current.includes(name) ? current.filter((item) => item !== name) : [...current, name]);
  }

  function toggleSkill(skill) {
    setChosen((current) => current.some((item) => item.id === skill.id)
      ? current.filter((item) => item.id !== skill.id)
      : [...current, skill]);
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const body = { ...form, languages: languages.join(", "), years_required: Number(form.years_required) || 0, skill_ids: chosen.map((skill) => skill.id) };
      if (editing) {
        await api(`/offers/${id}`, { method: "PUT", body });
        navigate("/offres");
        return;
      }
      const created = await api("/offers", { method: "POST", body });
      navigate(`/offres/${created.id}/candidatures`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Shell>
      <div className="page-head">
        <div>
          <div className="eyebrow">Entreprise</div>
          <h1>{editing ? "Modifier l'offre" : "Publier une offre"}</h1>
          <p>{editing ? "Corrigez le texte, la ville, les langues et les compétences." : "Les compétences affichées sont celles du domaine de l'entreprise."}</p>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      <form className="card" onSubmit={submit}>
        <label>Intitulé</label>
        <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
        <label>Ville</label>
        <select value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} required>
          {(MOROCCO_CITIES.includes(form.city) ? MOROCCO_CITIES : [form.city, ...MOROCCO_CITIES]).map((city) => <option key={city} value={city}>{city}</option>)}
        </select>
        <label>Domaine</label>
        <p>{company?.domain_name || "Aucun domaine. Il se choisit à l'inscription."}</p>
        <label>Description</label>
        <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <label>Diplôme demandé</label>
        <select value={form.diploma_level} onChange={(e) => setForm({ ...form, diploma_level: e.target.value })}>
          {LEVELS.map((level) => <option key={level} value={level}>{level || "Non précisé"}</option>)}
        </select>
        <label>Années d'expérience</label>
        <input type="number" min="0" step="0.5" value={form.years_required} onChange={(e) => setForm({ ...form, years_required: e.target.value })} />
        <label>Langues exigées</label>
        <p className="muted">Cliquez pour ajouter ou retirer une langue.</p>
        <div className="skill-cloud">
          {OFFER_LANGUAGES.map((name) => (
            <button type="button" key={name} className={languages.includes(name) ? "picked" : "secondary"} onClick={() => toggleLanguage(name)}>{name}</button>
          ))}
        </div>
        <label>Compétences exigées</label>
        <p className="muted">{company?.domain_name ? `Compétences du domaine ${company.domain_name}. Cliquez pour ajouter.` : "Le domaine de l'entreprise n'est pas enregistré."}</p>
        <input placeholder="Filtrer la liste" value={query} onChange={(e) => searchSkills(e.target.value)} />
        <div className="skill-cloud">
          {skills.map((skill) => {
            const selected = chosen.some((item) => item.id === skill.id);
            return <button type="button" className={selected ? "picked" : "secondary"} key={skill.id} onClick={() => toggleSkill(skill)}>{skill.label}</button>;
          })}
        </div>
        {company?.domain_id && skills.length === 0 && <p className="muted">Aucune compétence pour ce filtre.</p>}
        <p>{chosen.map((skill) => <span className="tag ok" key={skill.id}>{skill.label}</span>)}</p>
        <button className="wide" type="submit">{editing ? "Enregistrer" : "Publier"}</button>
      </form>
    </Shell>
  );
}

function OfferDetail() {
  const { id } = useParams();
  const [offer, setOffer] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [letter, setLetter] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [hasCv, setHasCv] = useState(null);
  const [coherence, setCoherence] = useState("");
  const [coherenceNote, setCoherenceNote] = useState("");
  const [phase, setPhase] = useState(-1);
  const [ready, setReady] = useState(false);
  const [marks, setMarks] = useState({});
  const [cancelled, setCancelled] = useState(false);
  const started = useRef(false);
  const analysisRun = useRef(null);
  const phases = [
    { title: "Lecture du CV", detail: "Le PDF déposé dans Mon profil est relu, phrase par phrase." },
    { title: "Compétences du poste", detail: "Chaque compétence demandée est cherchée telle qu'elle est écrite dans le CV.", key: "skills" },
    { title: "Expérience", detail: "Les périodes de stage datées sont additionnées.", key: "experience" },
    { title: "Diplôme", detail: "Un diplôme compte seulement s'il est obtenu, pas s'il est encore en cours.", key: "diploma" },
    { title: "Langues", detail: "Les langues écrites dans le CV sont comparées à celles du poste.", key: "languages" },
    { title: "Score sur 100", detail: "Compétences, expérience, diplôme et langues sont additionnés.", key: "total" },
  ];

  useEffect(() => {
    started.current = false;
    setAnalysis(null);
    setOffer(null);
    api("/offers").then((rows) => {
      const found = rows.find((row) => String(row.id) === id);
      setOffer(found || false);
      if (!found) setError("Offre introuvable");
    }).catch((err) => setError(err.message));
    api("/profile").then((profile) => {
      setHasCv(Boolean(profile.cv_filename && profile.cv_text));
      setCoherence(profile.coherence || "");
      setCoherenceNote(profile.coherence_note || "");
    }).catch(() => setHasCv(false));
  }, [id]);

  async function analyze() {
    const run = { stopped: false, controller: new AbortController(), cancelWait: null };
    analysisRun.current = run;
    setBusy(true);
    setCancelled(false);
    setReady(false);
    setAnalysis(null);
    setMarks({});
    setError("");
    setPhase(0);
    const pending = api(`/offers/${id}/analyze`, { method: "POST", signal: run.controller.signal });
    const wait = (ms) => new Promise((resolve, reject) => {
      if (run.stopped) {
        reject(new DOMException("Analyse arrêtée", "AbortError"));
        return;
      }
      const timer = setTimeout(() => {
        run.cancelWait = null;
        if (run.stopped) reject(new DOMException("Analyse arrêtée", "AbortError"));
        else resolve();
      }, ms);
      run.cancelWait = () => {
        clearTimeout(timer);
        reject(new DOMException("Analyse arrêtée", "AbortError"));
      };
    });
    try {
      let result = null;
      for (let index = 0; index < phases.length; index += 1) {
        if (run.stopped) throw new DOMException("Analyse arrêtée", "AbortError");
        setPhase(index);
        if (phases[index].key === "skills") {
          result = await pending;
          if (run.stopped) throw new DOMException("Analyse arrêtée", "AbortError");
          setAnalysis(result);
          setLetter(result.letter);
        }
        await wait(1800);
        if (run.stopped) throw new DOMException("Analyse arrêtée", "AbortError");
        if (phases[index].key) setMarks((current) => ({ ...current, [phases[index].key]: true }));
      }
      setReady(true);
    } catch (err) {
      if (err.name === "AbortError") {
        setPhase(-1);
        setReady(false);
        setAnalysis(null);
        setMarks({});
        setCancelled(true);
      } else {
        setError(err.message);
        setPhase(-1);
      }
    } finally {
      analysisRun.current = null;
      setBusy(false);
    }
  }

  function stopAnalysis() {
    const run = analysisRun.current;
    if (!run) return;
    run.stopped = true;
    run.controller.abort();
    run.cancelWait?.();
  }

  useEffect(() => {
    if (!offer || offer.applied || coherence === "incoherent" || hasCv !== true || started.current) return;
    started.current = true;
    analyze();
  }, [offer, hasCv, coherence, id]);

  async function apply() {
    setBusy(true);
    setError("");
    try {
      await api(`/offers/${id}/apply`, { method: "POST", body: { letter } });
      window.location.href = "/candidatures";
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <Shell>
      {!offer ? <p>{error || "Chargement..."}</p> : (
        <>
          <div className="page-head">
            <div>
              <div className="eyebrow">{offer.domain_name || "Offre"}</div>
              <h1>{offer.title}</h1>
              <p>{offer.city}. L'analyse utilise le CV déposé dans Mon profil.</p>
            </div>
          </div>
          <p>{offer.description}</p>
          {error && <p className="error">{error}</p>}
          {offer.applied && (
            <section className="card">
              <p>Vous avez déjà postulé à cette offre. Une seule candidature est possible.</p>
              <Link className="button" to="/candidatures">Voir mes candidatures</Link>
            </section>
          )}
          {coherence === "incoherent" && !offer.applied && (
            <section className="card">
              <p>Votre domaine ne correspond pas à votre CV. Vous ne pouvez pas postuler.</p>
              {coherenceNote && <p>{coherenceNote}</p>}
              <Link className="button" to="/profil">Corriger Mon profil</Link>
            </section>
          )}
          {hasCv === false && !offer.applied && coherence !== "incoherent" && (
            <section className="card">
              <p>Déposez et analysez votre CV dans Mon profil avant de postuler.</p>
              <Link className="button" to="/profil">Ouvrir Mon profil</Link>
            </section>
          )}
          {hasCv && !offer.applied && coherence !== "incoherent" && phase >= 0 && (
            <section className="card analysis-board">
              <div className="analysis-head">
                <div>
                  <div className="eyebrow">{ready ? "Analyse terminée" : "Analyse en cours"}</div>
                  <h2>CV comparé à {offer.title}</h2>
                </div>
                <strong>{ready ? 100 : Math.round(((phase + 0.4) / phases.length) * 100)}%</strong>
              </div>
              <div className="meter" aria-hidden="true"><span style={{ width: `${ready ? 100 : ((phase + 0.4) / phases.length) * 100}%` }} /></div>
              <p className="phase-note">{phases[Math.min(phase, phases.length - 1)].detail}</p>
              {!ready && (
                <div className="actions">
                  <button type="button" className="danger" onClick={stopAnalysis}>Arrêter l'analyse</button>
                </div>
              )}
              <ol className="calc-steps">
                {phases.map((item, index) => (
                  <li key={item.title} className={index < phase || (ready && index === phase) ? "done" : index === phase ? "current" : ""}>
                    <span>{index < phase || ready ? "✓" : index === phase ? "…" : index + 1}</span>
                    <div>
                      <strong>{item.title}</strong>
                      <small>{index < phase || ready ? "Terminé" : index === phase ? "En cours" : "En attente"}</small>
                    </div>
                  </li>
                ))}
              </ol>
              {analysis && phase >= 1 && (
                <div className="score-panel">
                  <ScoreRing value={marks.total ? analysis.score : "…"} />
                  <div>
                    <div className="breakdown">
                      {[
                        ["skills", analysis.skill_points, "/50", `${analysis.matched_count} sur ${analysis.required_count} écrite(s) dans le CV`],
                        ["experience", analysis.experience_points, "/20", "Expérience"],
                        ["diploma", analysis.diploma_points, "/15", "Diplôme"],
                        ["languages", analysis.language_points, "/15", "Langues"],
                      ].map(([key, points, scale, label]) => (
                        <div key={key} className={marks[key] ? "shown" : "pending"}>
                          <b>{marks[key] ? points : "…"}{marks[key] && <small>{scale}</small>}</b>
                          <span>{label}</span>
                        </div>
                      ))}
                    </div>
                    {marks.total && <div className="actions">{analysis.reasons.map((reason) => <span className="tag" key={reason}>{reason}</span>)}</div>}
                  </div>
                </div>
              )}
            </section>
          )}
          {hasCv && !offer.applied && coherence !== "incoherent" && (error || cancelled) && !analysis && phase < 0 && (
            <button onClick={analyze} disabled={busy}>Relancer l'analyse</button>
          )}
          {ready && analysis && !offer.applied && coherence !== "incoherent" && (
            <div className="stack">
              <section className="card">
                <h3>Compétences de l'offre écrites dans le CV</h3>
                <p className="muted">Le mot demandé est à gauche. À droite, la phrase du CV qui le contient.</p>
                {analysis.acquired.length === 0 && <p>Aucune compétence demandée n'est écrite dans le CV.</p>}
                {analysis.acquired.map((item) => <p key={item.skill_id}><strong>{item.label}</strong> — {item.proof}</p>)}
                {analysis.missing.length > 0 && (
                  <>
                    <h3>Compétences demandées absentes du CV</h3>
                    {analysis.missing.map((item) => <p key={item.skill_id}>{item.label}</p>)}
                  </>
                )}
                {analysis.trainings.length > 0 && (
                  <>
                    <h3>Formations proposées pour combler ce qui manque</h3>
                    {analysis.trainings.map((item) => <p key={item.skill}>{item.title} · {item.duration}</p>)}
                  </>
                )}
              </section>
              <section className="card">
                <h3>Lettre</h3>
                <textarea value={letter} onChange={(e) => setLetter(e.target.value)} />
                <p className="actions">
                  <button onClick={apply} disabled={busy}>Envoyer la candidature</button>
                  <button type="button" className="secondary" onClick={() => downloadPdf("lettre.pdf", letter)}>Télécharger la lettre</button>
                </p>
              </section>
            </div>
          )}
        </>
      )}
    </Shell>
  );
}

const APPLICATION_STATUS = {
  envoyee: { label: "En attente", tag: "warn" },
  acceptee: { label: "Acceptée", tag: "ok" },
  refusee: { label: "Refusée", tag: "bad" },
};

function Applications({ company = false }) {
  const { id } = useParams();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [deciding, setDeciding] = useState(null);
  useEffect(() => {
    const path = company ? `/offers/${id}/applications` : "/applications";
    api(path).then(setRows).catch((err) => setError(err.message));
  }, [company, id]);

  async function decide(row, status) {
    setDeciding(row.id);
    setError("");
    try {
      const updated = await api(`/applications/${row.id}`, { method: "PATCH", body: { status } });
      setRows((current) => current.map((item) => (item.id === row.id ? { ...item, ...updated } : item)));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeciding(null);
    }
  }

  return (
    <Shell>
      <div className="page-head">
        <div>
          <div className="eyebrow">{company ? "Entreprise" : "Candidat"}</div>
          <h1>{company ? "Classement" : "Mes candidatures"}</h1>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="list">
        {rows.map((row) => (
          <article className="card" key={row.id}>
            <div className="offer-top">
              <h2>{company ? row.candidate_name : row.offer_title}</h2>
              <div className="offer-side">
                <span className={`tag ${APPLICATION_STATUS[row.status]?.tag || "warn"}`}>{APPLICATION_STATUS[row.status]?.label || "En attente"}</span>
                <ScoreRing value={row.score} />
              </div>
            </div>
            <p>{(row.reasons || []).map((reason) => <span className="tag" key={reason}>{reason}</span>)}</p>
            <pre className="letter">{row.summary}</pre>
            {row.letter && (
              <p className="actions">
                <button className="secondary" onClick={() => downloadPdf("lettre.pdf", row.letter)}>Télécharger la lettre</button>
                {company && (
                  <button className="secondary" onClick={() => downloadFile(`/applications/${row.id}/cv`, row.cv_filename || "cv.pdf").catch((err) => setError(err.message))}>
                    CV original
                  </button>
                )}
              </p>
            )}
            {company && (
              <p className="actions">
                <button onClick={() => decide(row, "acceptee")} disabled={deciding === row.id || row.status === "acceptee"}>Accepter</button>
                <button className="danger" onClick={() => decide(row, "refusee")} disabled={deciding === row.id || row.status === "refusee"}>Refuser</button>
              </p>
            )}
            {company && <pre className="letter">{row.letter}</pre>}
          </article>
        ))}
        {rows.length === 0 && <p className="empty">Aucune candidature.</p>}
      </div>
    </Shell>
  );
}

function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api("/admin/dashboard").then(setData).catch((err) => setError(err.message)); }, []);
  if (!data) return <Shell><p>{error || "Chargement..."}</p></Shell>;
  return (
    <Shell>
      <div className="page-head">
        <div>
          <div className="eyebrow">Administrateur</div>
          <h1>Tableau de bord</h1>
          <p>Les métiers demandés, les compétences absentes et les offres sans bon profil.</p>
        </div>
      </div>
      <div className="grid">
        <article className="card stat-card"><div className="stat">{data.candidates}</div><span>Candidats</span></article>
        <article className="card stat-card"><div className="stat">{data.entreprises}</div><span>Entreprises</span></article>
        <article className="card stat-card"><div className="stat">{data.offers}</div><span>Offres en ligne</span></article>
        <article className="card stat-card"><div className="stat">{data.incoherent_profiles}</div><span>Profils incohérents</span></article>
      </div>
      <div className="stack">
      <section className="card">
        <h2>Métiers les plus demandés</h2>
        {data.demanded_domains.length === 0 && <p className="muted">Aucune offre publiée.</p>}
        {data.demanded_domains.map((item) => <p key={item.name}>{item.name} · {item.offers} offre(s)</p>)}
      </section>
      <section className="card">
        <h2>Compétences souvent absentes</h2>
        {data.often_missing.length === 0 && <p className="muted">Aucune candidature analysée.</p>}
        {data.often_missing.map((item) => <p key={item.label}>{item.label} · {item.count}</p>)}
      </section>
      <section className="card">
        <h2>Offres sans profil au-dessus de 60</h2>
        {data.offers_without_fit.map((item) => <p key={item.id}>{item.title} · meilleur score {item.best_score ?? "aucun"}</p>)}
      </section>
      </div>
    </Shell>
  );
}

function Alerts() {
  const [rows, setRows] = useState([]);
  useEffect(() => { api("/admin/alerts").then(setRows); }, []);
  return (
    <Shell>
      <div className="page-head">
        <div>
          <div className="eyebrow">Administrateur</div>
          <h1>Alertes de cohérence</h1>
        </div>
      </div>
      <div className="list">
        {rows.map((row) => (
          <article className="card" key={row.user_id}>
            <h2>{row.name}</h2>
            <p><span className="tag bad">{row.coherence}</span> {row.domain}</p>
            <p>{row.note}</p>
          </article>
        ))}
        {rows.length === 0 && <p className="empty">Aucune alerte.</p>}
      </div>
    </Shell>
  );
}

const EMPTY_USER = { full_name: "", email: "", password: "", role: "candidate", is_active: true };

function Accounts() {
  const me = currentUser();
  const [users, setUsers] = useState([]);
  const [userForm, setUserForm] = useState(EMPTY_USER);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(null);
  const [removing, setRemoving] = useState(false);

  function loadUsers() { return api("/admin/users").then(setUsers); }

  useEffect(() => {
    loadUsers().catch((err) => setError(err.message));
  }, []);

  async function saveUser(event) {
    event.preventDefault();
    setError("");
    const body = { full_name: userForm.full_name, email: userForm.email, password: userForm.password, role: userForm.role, is_active: userForm.is_active };
    try {
      await api("/admin/users", { method: "POST", body });
      setUserForm(EMPTY_USER);
      await loadUsers();
    } catch (err) { setError(err.message); }
  }

  async function confirmRemove() {
    if (!pending) return;
    setRemoving(true);
    setError("");
    try {
      await api(`/admin/users/${pending.id}`, { method: "DELETE" });
      setPending(null);
      await loadUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setRemoving(false);
    }
  }

  return (
    <Shell>
      <div className="page-head">
        <div>
          <div className="eyebrow">Administrateur</div>
          <h1>Comptes</h1>
          <p>Créer un compte ou supprimer un compte existant. Un compte déjà créé ne se modifie pas.</p>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      <form className="card form-grid" onSubmit={saveUser}>
        <h2>Nouveau compte</h2>
        <div className="field-row">
          <div><label>Nom</label><input value={userForm.full_name} onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })} required /></div>
          <div><label>E-mail</label><input type="email" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} required /></div>
        </div>
        <div className="field-row">
          <div><label>Rôle</label>
            <select value={userForm.role} onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}>
              <option value="candidate">Candidat</option>
              <option value="entreprise">Entreprise</option>
              <option value="admin">Administrateur</option>
            </select>
          </div>
          <div><label>Mot de passe</label><input type="password" value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} required minLength={6} /></div>
        </div>
        <label className="check"><input type="checkbox" checked={userForm.is_active} onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })} /> Compte actif</label>
        <div className="actions">
          <button type="submit">Créer</button>
        </div>
      </form>
      <div className="card table-wrap">
        <table>
          <thead><tr><th>Nom</th><th>E-mail</th><th>Rôle</th><th>Statut</th><th className="row-action">Action</th></tr></thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.full_name}</td>
                <td>{user.email}</td>
                <td>{ROLE_LABEL[user.role] || user.role}</td>
                <td>{user.is_active ? "Actif" : "Désactivé"}</td>
                <td className="row-action">
                  {user.id !== me?.id
                    ? <button type="button" className="danger" onClick={() => setPending(user)}>Supprimer</button>
                    : <span className="muted">Votre compte</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pending && (
        <div className="modal-backdrop" onClick={() => { if (!removing) setPending(null); }}>
          <div className="modal card" role="dialog" aria-modal="true" aria-labelledby="delete-title" onClick={(event) => event.stopPropagation()}>
            <div className="eyebrow">Confirmation</div>
            <h2 id="delete-title">Supprimer ce compte</h2>
            <p>Le compte de <strong>{pending.full_name}</strong> sera retiré de la plateforme. Cette action est définitive.</p>
            <div className="modal-actions">
              <button type="button" className="secondary" onClick={() => setPending(null)} disabled={removing}>Annuler</button>
              <button type="button" className="danger solid" onClick={confirmRemove} disabled={removing}>Supprimer</button>
            </div>
          </div>
        </div>
      )}
    </Shell>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/connexion" element={<Login />} />
      <Route path="/registre" element={<Register />} />
      <Route path="/profil" element={<Profile />} />
      <Route path="/offres" element={<Offers />} />
      <Route path="/offres/nouvelle" element={<NewOffer />} />
      <Route path="/offres/:id/modifier" element={<NewOffer editing />} />
      <Route path="/offres/:id" element={<OfferDetail />} />
      <Route path="/offres/:id/candidatures" element={<Applications company />} />
      <Route path="/candidatures" element={<Applications />} />
      <Route path="/admin" element={<Dashboard />} />
      <Route path="/admin/alertes" element={<Alerts />} />
      <Route path="/admin/gestion" element={<Accounts />} />
      <Route path="/admin/comptes" element={<Accounts />} />
    </Routes>
  );
}
