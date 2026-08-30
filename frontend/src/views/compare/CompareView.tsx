/**
 * Compare — placeholder.
 *
 * This whole folder belongs to the Compare feature agent: routes, navigation,
 * providers, shared components and styles are already wired, so implementing
 * the view means editing only files under `src/views/compare/`.
 *
 * Useful hooks already available:
 *   - `api` from '../../api' (real M9 client or the deterministic mock)
 *   - `useScenarioContextEffect` to fill the top-bar scenario slot
 *   - `useDrawer().setDrawerContent` to publish provenance into the drawer
 *   - `useToast` for terminal-state notifications
 *   - `.view-compare` styles are ported in `src/styles/views.css`
 */
export function CompareView() {
  return (
    <section className="view view-compare">
      <div className="wrap" style={{ padding: '28px 32px' }}>
        <h1 style={{ fontSize: 21, fontWeight: 700 }}>Compare</h1>
      </div>
    </section>
  );
}
