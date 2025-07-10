import '../PicoOptions/Options.css'

export function getChannelRowClass(active, anyActive, channelSetup = false) {
  let background = '';
  if (!anyActive && channelSetup) {
    background = 'bg-red';
  } else {
    background = active ? 'bg-green' : 'bg-red';
  }
  if (channelSetup && background === 'bg-red') {
    return 'bg-grey';
  }
  return background;
}

export function toSiUnit(num) {
  let numin = num;
  const pow = [-15, -12, -9, -6, -3, 0];
  const siUnit = ['f', 'p', 'n', 'μ', 'm', ''];
  let i = 5;
  const isNegative = numin < 0;

  if (isNegative) {
    numin = -numin;
  }

  let testnum = numin / Math.pow(10, pow[i]);
  while (testnum < 1 && i > 0) {
    i -= 1;
    testnum = numin / Math.pow(10, pow[i]);
  }

  const formatted = testnum.toFixed(2) + ' ' + siUnit[i];
  return isNegative ? '-' + formatted : formatted;
}
