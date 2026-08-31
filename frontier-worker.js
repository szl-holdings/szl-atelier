const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

function randomFrom(seed) {
  let state = (seed >>> 0) || 0x9e3779b9;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}

function sigmoid(value) {
  if (value >= 0) return 1 / (1 + Math.exp(-value));
  const exp = Math.exp(value);
  return exp / (1 + exp);
}

function probability(weights, bias, features) {
  let score = bias;
  for (let i = 0; i < weights.length; i += 1) score += weights[i] * features[i];
  return sigmoid(score);
}

function binaryLoss(probabilityValue, target) {
  const p = clamp(probabilityValue, 1e-7, 1 - 1e-7);
  return -(target * Math.log(p) + (1 - target) * Math.log(1 - p));
}

function evaluate(weights, bias, rows, threshold) {
  let binaryCorrect = 0;
  let selectiveCorrect = 0;
  let covered = 0;
  let loss = 0;
  let preserveTotal = 0;
  let preserveCount = 0;
  let counterfactualTotal = 0;
  let counterfactualCount = 0;
  let overclaims = 0;

  for (const row of rows) {
    const p = probability(weights, bias, row.x);
    loss += binaryLoss(p, row.y);
    if ((p >= 0.5 ? 1 : 0) === row.y) binaryCorrect += 1;
    const decision = p >= threshold ? 1 : p <= 1 - threshold ? 0 : null;
    if (decision !== null) {
      covered += 1;
      if (decision === row.y) selectiveCorrect += 1;
    }
    if (row.group === "preserve") {
      preserveTotal += p;
      preserveCount += 1;
    } else {
      counterfactualTotal += p;
      counterfactualCount += 1;
      if (p >= 0.8) overclaims += 1;
    }
  }

  const preserveMean = preserveCount ? preserveTotal / preserveCount : 0;
  const counterfactualMean = counterfactualCount ? counterfactualTotal / counterfactualCount : 0;
  return {
    accuracy: binaryCorrect / rows.length,
    selectiveAccuracy: covered ? selectiveCorrect / covered : 0,
    coverage: covered / rows.length,
    loss: loss / rows.length,
    margin: preserveMean - counterfactualMean,
    overclaimRate: counterfactualCount ? overclaims / counterfactualCount : 0,
  };
}

function train(payload) {
  const { lane, trainRows, testRows, config, seed } = payload;
  const random = randomFrom(seed ^ lane.seedSalt);
  const dimensions = trainRows[0].x.length;
  const weights = Array.from({ length: dimensions }, () => (random() - 0.5) * 0.08);
  let bias = lane.bias;
  const losses = [];

  for (let epoch = 0; epoch < config.epochs; epoch += 1) {
    const order = Array.from({ length: trainRows.length }, (_, index) => index);
    for (let i = order.length - 1; i > 0; i -= 1) {
      const j = Math.floor(random() * (i + 1));
      const swap = order[i];
      order[i] = order[j];
      order[j] = swap;
    }

    let epochLoss = 0;
    for (const rowIndex of order) {
      const row = trainRows[rowIndex];
      const p = probability(weights, bias, row.x);
      const sampleWeight = row.y ? 0.5 + config.evidence : 0.5 + config.abstain;
      const error = clamp((p - row.y) * sampleWeight, -2, 2);
      for (let feature = 0; feature < dimensions; feature += 1) {
        const regularization = lane.l2 * config.stability * weights[feature];
        weights[feature] -= lane.learningRate * (error * row.x[feature] + regularization);
      }
      bias -= lane.learningRate * error;
      epochLoss += binaryLoss(p, row.y);
    }
    losses.push(epochLoss / trainRows.length);
  }

  const trainMetrics = evaluate(weights, bias, trainRows, lane.threshold);
  const testMetrics = evaluate(weights, bias, testRows, lane.threshold);
  const generalization = Math.max(0, 1 - Math.abs(trainMetrics.accuracy - testMetrics.accuracy));
  const denominator = config.evidence + config.abstain + config.stability + 1;
  const rawReward =
    (config.evidence * Math.max(0, testMetrics.margin) +
      config.abstain * (1 - testMetrics.overclaimRate) +
      config.stability * generalization +
      testMetrics.accuracy) /
    denominator;
  const flags = [];
  if (trainMetrics.accuracy - testMetrics.accuracy > 0.12) flags.push("GENERALIZATION_GAP");
  if (testMetrics.overclaimRate > 0.2) flags.push("COUNTERFACTUAL_OVERCLAIM");
  if (trainMetrics.accuracy > 0.95 && testMetrics.accuracy < 0.75) flags.push("TRAIN_TEST_DIVERGENCE");
  const reward = Math.max(0, rawReward - flags.length * 0.05);

  return {
    id: lane.id,
    label: lane.label,
    reward,
    train: trainMetrics,
    test: testMetrics,
    flags,
    losses,
    weights,
    bias,
    threshold: lane.threshold,
  };
}

self.onmessage = (event) => {
  try {
    self.postMessage({ ok: true, result: train(event.data) });
  } catch (error) {
    self.postMessage({ ok: false, error: error instanceof Error ? error.message : "Training worker failed" });
  }
};
