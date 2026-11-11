export function createLatestRequestGate() {
  let latest = 0;

  return {
    begin() {
      latest += 1;
      return latest;
    },

    isCurrent(request) {
      return request === latest;
    },
  };
}
