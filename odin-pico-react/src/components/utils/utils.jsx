import '../PicoOptions/Options.css'

export function getChannelRowClass(active, anyActive, channelSetup = false) {
  if (channelSetup && !anyActive) return 'bg-grey';
  if (active) return 'bg-green';
  return channelSetup ? 'bg-grey' : 'bg-red';
}

export function toSiUnit(num) {
  let numin = num;
  const pow = [-18, -15, -12, -9, -6, -3, 0, 3, 6, 9, 12, 15, 18];
  const siUnit = ['a', 'f', 'p', 'n', 'μ', 'm', '', 'k', 'M', 'G', 'T', 'P', 'E'];
  let i = 6; // start at 0 exponent
  const isNegative = numin < 0;

  if (isNegative) {
    numin = -numin;
  }

  let testnum = numin / Math.pow(10, pow[i]);
  while (testnum < 1 && i > 0) {
    i -= 1;
    testnum = numin / Math.pow(10, pow[i]);
  }
  while (testnum >= 1000 && i < pow.length - 1) {
    i += 1;
    testnum = numin / Math.pow(10, pow[i]);
  }

  const formatted = testnum.toFixed(0) + siUnit[i];
  return isNegative ? '-' + formatted : formatted;
}

