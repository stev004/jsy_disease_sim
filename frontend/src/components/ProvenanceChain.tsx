import type { JobStatusResponse } from '../api';
import { useToast } from './Toast';

interface HashNode {
  key: string;
  label: string;
  value: string | null | undefined;
}

export function ProvenanceChain({ job, running }: { job: JobStatusResponse; running: boolean }) {
  const { showToast } = useToast();
  const nodes: HashNode[] = [
    { key: 'scenario_hash', label: 'Scenario', value: job.scenario_hash },
    { key: 'latent_hash', label: 'Latent outcome', value: job.latent_hash },
    { key: 'bundle_hash', label: 'Artifact bundle', value: job.bundle_hash },
    { key: 'result_manifest_hash', label: 'Result manifest', value: job.result_manifest_hash },
    { key: 'engine_git_commit', label: 'Engine Git commit', value: job.engine_git_commit },
  ];

  const copy = async (node: HashNode) => {
    if (!node.value) return;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(node.value);
      showToast({
        tone: 'neutral',
        title: `${node.label} copied`,
        body: node.value,
        timeout: 4_000,
      });
    } catch (e) {
      showToast({
        tone: 'bad',
        title: e instanceof Error && e.message === 'Clipboard unavailable'
          ? 'Clipboard unavailable'
          : `Could not copy the ${node.label.toLowerCase()}`,
        body: node.value,
      });
    }
  };

  return (
    <div className="runs-chain-wrap">
      <div className="runs-chain" aria-label="Provenance hash chain">
        {nodes.map((node, index) => (
          <div className="runs-chain-item" key={node.key}>
            <button
              type="button"
              className={`runs-chain-node${node.value ? '' : ' unpublished'}`}
              disabled={!node.value}
              title={node.value ? `${node.value} — click to copy` : `${node.label}: not published`}
              aria-label={node.value ? `Copy ${node.label} hash ${node.value}` : `${node.label}: not published`}
              onClick={() => void copy(node)}
            >
              <span className="runs-chain-label">{node.label}</span>
              <span className={`runs-chain-value ${node.value ? 'mono' : ''}`}>
                {node.value ? shortHash(node.value) : 'not published'}
              </span>
            </button>
            {index < nodes.length - 1 && (
              <svg className="runs-chain-link" width="28" height="20" viewBox="0 0 28 20" aria-hidden="true">
                <line
                  className={`hash-chain-connector${running ? ' running' : ''}`}
                  x1="1"
                  y1="10"
                  x2="27"
                  y2="10"
                  stroke="var(--accent)"
                  strokeWidth="2"
                />
              </svg>
            )}
          </div>
        ))}
        <VerificationChip value={job.verification_status} />
      </div>
    </div>
  );
}

function VerificationChip({ value }: { value: string | null | undefined }) {
  const state = value?.toLowerCase();
  if (state === 'passed' || state === 'pass') {
    return <span className="runs-verify-chip good">Verification · {value}</span>;
  }
  if (state === 'failed' || state === 'fail') {
    return <span className="runs-verify-chip bad">Verification · {value}</span>;
  }
  return <span className="runs-verify-chip unpublished">Verification · {value ?? 'not published'}</span>;
}

function shortHash(value: string): string {
  return value.length > 12 ? `${value.slice(0, 8)}…${value.slice(-4)}` : value;
}
