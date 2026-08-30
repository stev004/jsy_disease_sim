/**
 * Body of the "Assumptions & sources" drawer (design §10).
 *
 * Synthetic-model note → verification block (finalizer status, engine commit +
 * dirty flag, Starsim version, request/scenario/latent/bundle hashes, each
 * truncated and click-to-copy) → parameter-provenance table → badge legend →
 * map attribution.
 *
 * The verification values are read from a real job: whichever job a view
 * announced through `provenanceStore`, else the newest succeeded job.
 */

import { useEffect, useState } from 'react';
import { api } from '../../api';
import type { CapabilitiesResponse, JobStatusResponse, JsonObject } from '../../api/types';
import { Badge, PROVENANCE_MEANING, type Provenance } from '../../components/Badge';
import { useToast } from '../../components/Toast';
import { OSM_ATTRIBUTION } from '../../map/geometry';
import { useProvenanceJobId } from './provenanceStore';
import './drawer.css';

/* ======================== static design content ======================== */

/** Parameter provenance rows — design content, identical for every run. */
const PROVENANCE_ROWS: Array<[string, string, Provenance, boolean]> = [
  ['Parish population & households', 'Census 2021', 'observed', false],
  ['Annual air / ferry arrivals', '720,842 / 196,623', 'observed', true],
  ['School FTE controls', 'CYPES', 'observed', false],
  ['Care staffing ratios', 'Regulatory minima', 'derived', false],
  ['Latent / infectious periods', '2.0 d / 5.0 d', 'literature', true],
  ['Transmissibility (β)', '0.08', 'assumption', true],
  ['Intervention adherence', '80%', 'assumption', true],
  ['Visitor seasonality', 'Summer-peaked', 'assumption', false],
  ['Detection probability', '38%', 'assumption', true],
];

const LEGEND: Provenance[] = ['observed', 'derived', 'literature', 'calibrated', 'assumption'];

/* ============================== helpers ============================== */

/** `9c41d2c07b…5c6b0a3f2e1d0c88af` → `9c41d2…88af`. */
function truncateMiddle(value: string, head = 6, tail = 4): string {
  if (value.length <= head + tail + 1) return value;
  return `${value.slice(0, head)}…${value.slice(-tail)}`;
}

function engineString(engine: JsonObject | undefined, key: string): string | null {
  const v = engine?.[key];
  return typeof v === 'string' && v.trim() ? v : null;
}

/* ============================== the body ============================== */

export function ProvenanceContent() {
  const announced = useProvenanceJobId();
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [caps, setCaps] = useState<CapabilitiesResponse | null>(null);
  const [failed, setFailed] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    let cancelled = false;
    setFailed(false);
    (async () => {
      try {
        if (announced) {
          const j = await api.getJob(announced);
          if (!cancelled) setJob(j);
          return;
        }
        const res = await api.listJobs({ state: 'SUCCEEDED', limit: 50 });
        if (cancelled) return;
        const newest = [...res.jobs].sort((a, b) =>
          (b.finished_at ?? b.created_at).localeCompare(a.finished_at ?? a.created_at),
        )[0];
        setJob(newest ?? null);
      } catch {
        if (!cancelled) {
          setJob(null);
          setFailed(true);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [announced]);

  useEffect(() => {
    let cancelled = false;
    api
      .capabilities()
      .then((c) => {
        if (!cancelled) setCaps(c);
      })
      .catch(() => {
        if (!cancelled) setCaps(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const copy = (label: string, value: string) => {
    const write = navigator.clipboard?.writeText(value);
    if (!write) {
      showToast({ tone: 'bad', title: 'Clipboard unavailable', body: value });
      return;
    }
    write
      .then(() => showToast({ tone: 'neutral', title: `${label} copied`, body: value, timeout: 4000 }))
      .catch(() =>
        showToast({ tone: 'bad', title: `Could not copy the ${label.toLowerCase()}`, body: value }),
      );
  };

  const engine = caps?.engine as JsonObject | undefined;
  const commit = job?.engine_git_commit ?? engineString(engine, 'git_commit');
  const dirty = job?.dirty_worktree_flag ?? (engine?.dirty_worktree as boolean | undefined);
  const starsim = engineString(engine, 'starsim') ?? engineString(engine, 'starsim_version');
  const verification = job?.verification_status ?? null;

  const hashes: Array<[string, string | null | undefined]> = [
    ['Request hash', job?.request_hash],
    ['Scenario hash', job?.scenario_hash],
    ['Latent outcome hash', job?.latent_hash],
    ['Artifact bundle hash', job?.bundle_hash],
    ['Result manifest hash', job?.result_manifest_hash],
  ];

  return (
    <>
      <div className="dnote">
        This is a <b>synthetic research simulation</b> of a generated Jersey population. It is not a
        forecast, a surveillance product, or a policy recommendation. No real people are represented.
      </div>

      <div className="dsec">
        <h2>Verification</h2>

        {verification === 'passed' ? (
          <div className="verify-ok">✓ All artifacts verified by the result finalizer</div>
        ) : verification ? (
          <div className="prov-verify-other">Finalizer verification: {verification}</div>
        ) : (
          <div className="dnote">
            {failed
              ? 'The API could not be reached, so no verification status is available.'
              : job
                ? 'This job published no verification status.'
                : 'No completed run yet — open or submit a run to see its verification.'}
          </div>
        )}

        <div className="kv" style={{ marginTop: 10 }}>
          <div className="li">
            <span className="k">Engine commit</span>
            <span className="v mono">
              {commit ? `${commit} · ${dirty ? 'dirty worktree' : 'clean worktree'}` : 'not reported'}
            </span>
          </div>
          <div className="li">
            <span className="k">Starsim</span>
            <span className="v mono">{starsim ? `${starsim} · pinned` : 'not reported'}</span>
          </div>
          {hashes.map(([label, value]) =>
            value ? (
              <div className="li" key={label}>
                <span className="k">{label}</span>
                <button
                  type="button"
                  className="v mono prov-copy"
                  title={`${value} — click to copy`}
                  onClick={() => copy(label, value)}
                >
                  {truncateMiddle(value)}
                </button>
              </div>
            ) : null,
          )}
        </div>
        {job && (
          <div className="prov-jobline mono">
            {job.job_id} · {job.kind}
          </div>
        )}
      </div>

      <div className="dsec">
        <h2>Parameter provenance</h2>
        {PROVENANCE_ROWS.map(([name, value, kind, numeric]) => (
          <div className="prov-row" key={name}>
            <span>{name}</span>
            <span className={`v${numeric ? ' num' : ''}`}>{value}</span>
            <Badge kind={kind} />
          </div>
        ))}
      </div>

      <div className="dsec">
        <h2>What the labels mean</h2>
        <div className="kv">
          {LEGEND.map((k) => (
            <div className="li" key={k}>
              <span className="k">
                <Badge kind={k} />
              </span>
              <span className="v" style={{ fontWeight: 400, color: 'var(--ink-2)' }}>
                {PROVENANCE_MEANING[k]}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="dsec">
        <h2>Map</h2>
        <div className="dnote">{OSM_ATTRIBUTION}</div>
      </div>
    </>
  );
}
