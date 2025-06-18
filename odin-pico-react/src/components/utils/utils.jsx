export function getChannelRowClass(active, anyActive) {
  if (!anyActive) return 'table-danger';
  return active ? 'table-success' : 'table-danger';
}