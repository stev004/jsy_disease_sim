/**
 * Home — first-run orientation: see Jersey, start a scenario, reopen recent
 * results. Copy is ported from the M10 design mockup.
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api';
import { jobDisplayName, jobMetaLine } from '../../api/naming';
import type { JobStatusResponse } from '../../api/types';
import { Btn } from '../../components/Btn';
import { Card } from '../../components/Card';
import { StateChip } from '../../components/Chip';
import { JerseyMap } from '../../components/JerseyMap';
import { Label } from '../../components/Label';
import { CLAIM_BOUNDARY } from '../../app/AppShell';
import { ISLAND_POP, OSM_ATTRIBUTION, PARISHES } from '../../map/geometry';

const STEPS = [
  {
    n: '01',
    title: 'Define a scenario',
    body: 'Accept the defaults or add interventions and travel settings. A first run needs almost no decisions.',
  },
  {
    n: '02',
    title: 'Run it',
    body: 'Jobs run locally in the background with honest phase-by-phase status. Long runs are normal.',
  },
  {
    n: '03',
    title: 'Explore & compare',
    body: 'Watch the outbreak on the map, see which routes drive transmission, and compare matched scenarios.',
  },
];

const POP_TEXT = ISLAND_POP.toLocaleString('en-GB');

export function HomeView() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobStatusResponse[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .listJobs({ limit: 5 })
      .then((res) => {
        if (!cancelled) setJobs(res.jobs);
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const lastSucceeded = jobs.find((j) => j.state === 'SUCCEEDED');

  const openResults = (job: JobStatusResponse) => {
    navigate(job.kind === 'scenario_compare' ? `/compare/${job.job_id}` : `/results/${job.job_id}`);
  };

  return (
    <section className="view view-home">
      <div className="home-wrap">
        <div className="home-hero">
          <div className="home-map card mapground">
            <JerseyMap
              className="home-map-graphic"
              colorFor={() => 'var(--panel-2)'}
              labels
              scalebar
              ariaLabel="Map of the twelve parishes of Jersey"
            />
            <div className="home-hero-copy">
              <Label style={{ marginBottom: 10 }}>
                Synthetic epidemiology · Jersey, Channel Islands
              </Label>
              <h1>A synthetic Jersey. Many possible outbreak paths.</h1>
              <p className="home-population num">{POP_TEXT} synthetic residents</p>
              <p className="home-intro">
                Explore how a generic respiratory infection moves through households, schools,
                workplaces, care settings and travel.
              </p>
              <div className="cta">
                <Btn variant="primary" onClick={() => navigate('/simulate')}>
                  New scenario
                </Btn>
                <Btn
                  onClick={() =>
                    lastSucceeded ? openResults(lastSucceeded) : navigate('/results')
                  }
                >
                  Open last results
                </Btn>
                <Btn variant="ghost" onClick={() => navigate('/simulate')}>
                  Browse templates
                </Btn>
              </div>
            </div>
            <div className="home-map-caption">
              Synthetic Jersey · {PARISHES.length} parishes · {POP_TEXT} agents
            </div>
          </div>
        </div>

        <div className="home-steps">
          {STEPS.map((s) => (
            <Card key={s.n} className="home-step-card">
              <div className="n">Step {s.n}</div>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </Card>
          ))}
        </div>

        <Card className="home-recent">
          <div className="home-recent-head">
            <h2>Recent runs</h2>
            <span className="home-recent-limit">Latest 5</span>
          </div>
          {jobs.length === 0 && (
            <div className="row home-empty" role="status">
              {loadError
                ? `Unable to load recent runs: ${loadError}`
                : 'No runs yet. Start with a new scenario.'}
            </div>
          )}
          {jobs.map((job) => (
            <div className="row home-run-row" key={job.job_id}>
              <StateChip state={job.state} />
              <div className="home-run-copy">
                <b>{jobDisplayName(job)}</b>
                <span>{jobMetaLine(job)}</span>
              </div>
              <span className="home-run-spacer" />
              {job.state === 'SUCCEEDED' ? (
                <Btn onClick={() => openResults(job)}>
                  {job.kind === 'scenario_compare' ? 'Open comparison' : 'Open results'}
                </Btn>
              ) : (
                <Btn onClick={() => navigate('/runs')}>View status</Btn>
              )}
            </div>
          ))}
        </Card>

        <div className="home-foot">
          <span>{CLAIM_BOUNDARY}</span>
          <span>No real people are modelled.</span>
          <span>{OSM_ATTRIBUTION}</span>
        </div>
      </div>
    </section>
  );
}
