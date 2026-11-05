/**
 * Shared utility for unified feasibility and risk status representation
 * across ExecutiveStrip, FeasibilitySection, and DecisionSection.
 */

export function formatFeasibilityStatus(status) {
  if (!status) {
    return {
      status: 'conditional',
      label: 'Conditional',
      badgeClass: 'feas-unknown',
      stateTextClass: 'state-medium',
      summaryText: 'Conditional Review',
    };
  }

  const s = String(status).trim().toLowerCase();

  if (s === 'pass') {
    return {
      status: 'pass',
      label: 'Feasible',
      badgeClass: 'feas-pass',
      stateTextClass: 'state-pass',
      summaryText: 'Compatible (Pass)',
    };
  }

  if (s === 'fail') {
    return {
      status: 'fail',
      label: 'Exceeded',
      badgeClass: 'feas-fail',
      stateTextClass: 'state-high',
      summaryText: 'Limits Exceeded (Fail)',
    };
  }

  return {
    status: 'conditional',
    label: 'Conditional',
    badgeClass: 'feas-unknown',
    stateTextClass: 'state-medium',
    summaryText: 'Conditional Review',
  };
}
