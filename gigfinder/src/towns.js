// Towns (lat/lon) around Sagunto, used to estimate distance for offers that don't carry coordinates.
export const TOWNS = [
  ['Sagunto', 39.6833, -0.2744], ['Puerto de Sagunto', 39.6362, -0.2336], ['Canet d\'en Berenguer', 39.6700, -0.2060],
  ['Valencia', 39.4699, -0.3763], ['Torrent', 39.4370, -0.4650], ['Paterna', 39.5030, -0.4400], ['Mislata', 39.4750, -0.4180],
  ['Burjassot', 39.5090, -0.4150], ['Alboraya', 39.4980, -0.3500], ['Gandia', 38.9680, -0.1800], ['Sueca', 39.2030, -0.3100],
  ['Cullera', 39.1650, -0.2530], ['Alzira', 39.1500, -0.4350], ['Xativa', 38.9900, -0.5200], ['Sagunt', 39.6833, -0.2744],
  ['Liria', 39.6290, -0.5960], ['Llíria', 39.6290, -0.5960], ['Requena', 39.4880, -1.1000], ['Utiel', 39.5680, -1.2060],
  ['Moncada', 39.5450, -0.3950], ['Puçol', 39.6180, -0.3030], ['Puzol', 39.6180, -0.3030], ['El Puig', 39.5880, -0.3010],
  ['Segorbe', 39.8520, -0.4950], ['Jérica', 39.9210, -0.5700], ['Vall d\'Uixó', 39.8250, -0.2300], ['Vila-real', 39.9380, -0.1010],
  ['Castellón', 39.9864, -0.0513], ['Castelló', 39.9864, -0.0513], ['Burriana', 39.8890, -0.0850], ['Onda', 39.9650, -0.2560],
  ['Benicasim', 40.0560, 0.0670], ['Oropesa', 40.0920, 0.1400], ['Vinaròs', 40.4700, 0.4750], ['Peñíscola', 40.3590, 0.4080],
  ['Teruel', 40.3440, -1.1070], ['Albacete', 38.9940, -1.8580], ['Denia', 38.8400, 0.1050], ['Benidorm', 38.5400, -0.1310],
  ['Alicante', 38.3450, -0.4810], ['Elche', 38.2650, -0.6980], ['Torrevieja', 37.9780, -0.6820],
].map(([name, lat, lon]) => ({ name, lat, lon }));
