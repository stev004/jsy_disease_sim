/**
 * Runs — placeholder.
 *
 * This whole folder belongs to the Runs feature agent: routes, navigation,
 * providers, shared components and styles are already wired, so implementing
 * the view means editing only files under `src/views/runs/`.
 *
 * Useful hooks already available:
 *   - `api` from '../../api' (real M9 client or the deterministic mock)
 *   - `useScenarioContextEffect` to fill the top-bar scenario slot
 *   - `useDrawer().setDrawerContent` to publish provenance into the drawer
 *   - `useToast` for terminal-state notifications
 *   - `.view-runs` styles are ported in `src/styles/views.css`
 */
export function RunsView() {
  return (
    <section className="view view-runs">
      <div className="wrap" style={{ padding: '28px 32px' }}>
        <h1 style={{ fontSize: 21, fontWeight: 700 }}>Runs</h1>
      </div>
    </section>
  );
}
