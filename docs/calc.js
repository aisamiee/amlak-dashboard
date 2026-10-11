/* Feasibility engine — a line-for-line port of appraise() in scripts/valuation.py.
   Works in the browser (window.Calc) and in node (module.exports) so it can be tested against Python.
   Money in toman. */
(function (root) {
  'use strict';

  function unitSize(pNew) { return pNew >= 150e6 ? 130 : pNew >= 90e6 ? 115 : pNew >= 55e6 ? 100 : 85; }
  function hardCost(pNew) { return pNew >= 180e6 ? 50e6 : pNew >= 120e6 ? 46e6 : pNew >= 70e6 ? 42e6 : 35e6; }
  function pvFactor(rate) { return 0.4 + 0.3 / Math.pow(1 + rate, 0.5) + 0.3 / (1 + rate); }

  /**
   * @param {object} P   params from data.json (market.py constants)
   * @param {object} x   inputs: area, rate (toman/m2 land), premium, pNew, facts{floors,far,shape,adj,cost_mult,net_ratio},
   *                     optional overrides: extraFloor, costK, priceK, hardPpm, builderShare, capitalCost,
   *                     months, builderTarget, ownerTarget, saleHaircut, payment ('inst'|'cash')
   */
  function appraise(P, x) {
    const f = x.facts || {};
    const pNew = x.pNew;
    const shape = f.shape != null ? f.shape : 1.0;
    let floors, far;
    if (f.far) { far = f.far; floors = f.floors || Math.max(1, Math.round(far / P.OCCUPANCY)); }
    else { floors = f.floors; far = P.OCCUPANCY * floors; }
    if (x.extraFloor) { floors += 1; far += P.OCCUPANCY; }
    const area = x.area;
    const footprint = area * P.OCCUPANCY * shape;
    const gross = area * far * shape;
    const net = gross * (f.net_ratio != null ? f.net_ratio : P.NET_TO_GROSS);
    const usize = unitSize(pNew);
    const units = Math.max(floors, Math.round(net / usize));
    const groundSpaces = Math.floor(footprint / P.PARK_GROUND_M2);
    const needBasement = units > groundSpaces;
    let basement = needBasement ? (units - groundSpaces) * P.PARK_BASEMENT_M2 : 0;
    basement = needBasement ? Math.min(basement, area * 0.9) : 0;

    const haircut = x.saleHaircut != null ? x.saleHaircut : P.SALE_HAIRCUT;
    const salePpm = pNew * haircut * (1 + (f.adj || 0)) * (x.priceK || 1);
    const gdv = net * salePpm;
    const hc = (x.hardPpm != null ? x.hardPpm : hardCost(pNew)) * (x.costK || 1) * (f.cost_mult || 1);
    const hard = (gross + footprint * P.PILOTI_COST_FACTOR + basement * P.BASEMENT_COST_FACTOR) * hc;
    const extraFee = x.extraFloor ? area * P.OCCUPANCY * shape * P.NET_TO_GROSS * salePpm * P.EXTRA_FLOOR_FEE : 0;
    const soft = gdv * P.PERMIT_GDV + hard * P.ENGINEERING + extraFee;
    const cont = hard * P.CONTINGENCY;
    const sell = gdv * P.SELLING;
    const buildCost = hard + soft + cont;
    const cash = x.payment === 'cash';
    const landRate = x.rate * (1 + (x.premium || 0)) * (cash ? 0.9 : 1);
    const land = area * landRate * (1 + P.LAND_TXN);
    const total = land + buildCost + sell;
    const profit = gdv - total;
    const margin = total ? profit / total : null;
    const months = x.months || P.MONTHS;
    const targetProfit = P.TARGET_PROFIT;
    const landMax = gdv / (1 + targetProfit) - (buildCost + sell);
    const rlv = area ? landMax / (area * (1 + P.LAND_TXN)) : null;
    const breakeven = net ? total / net : null;
    const years = months / 12;
    const stress = (pk, ck) => { const g = gdv * pk; const t = land + buildCost * ck + g * P.SELLING; return (g - t) / t; };

    // ---- partnership ----
    const bs = x.builderShare != null ? x.builderShare : P.PARTNER_BUILDER_SHARE;
    const bTarget = x.builderTarget != null ? x.builderTarget : P.BUILDER_TARGET;
    const oTarget = x.ownerTarget != null ? x.ownerTarget : P.OWNER_TARGET;
    const ownerM2 = net * (1 - bs), builderM2 = net * bs;
    const ownerValue = ownerM2 * salePpm;
    const ownerCost = land;
    const ownerRet = ownerCost ? ownerValue / ownerCost - 1 : null;
    const pYears = (months + 3) / 12;
    const ann = r => (r != null && r > -1) ? Math.pow(1 + r, 1 / pYears) - 1 : null;
    const pv = cash ? 1 : pvFactor(x.capitalCost != null ? x.capitalCost : P.CAPITAL_COST);
    const ownerCostEff = ownerCost * pv;
    const ownerRetEff = ownerCostEff ? ownerValue / ownerCostEff - 1 : null;
    const builderRev = builderM2 * salePpm;
    const builderCost = buildCost + builderRev * P.SELLING;
    const builderMargin = builderCost ? builderRev / builderCost - 1 : null;
    const bsNeeded = gdv ? (buildCost * (1 + bTarget)) / (gdv * (1 - (1 + bTarget) * P.SELLING)) : null;
    const ownerFair = bsNeeded != null ? 1 - bsNeeded : null;
    const ownerRealShare = ownerFair != null ? Math.min(1 - bs, Math.max(0, ownerFair)) : 0;
    const ownerRealValue = net * ownerRealShare * salePpm;
    const ownerRealRetEff = ownerCostEff ? ownerRealValue / ownerCostEff - 1 : null;
    const maxBidPartner = area ? ownerRealValue / ((1 + oTarget) * pv * (1 + P.LAND_TXN) * area) / (cash ? 0.9 : 1) : null;

    return {
      floors, far: Math.round(far * shape * 100) / 100, shape, footprint, gross, net, unitSize: usize, units,
      groundSpaces, basement, needBasement, salePpm, gdv, hardPpm: hc, hard, soft: soft + cont, selling: sell,
      buildCost, buildCostPerNet: net ? buildCost / net : null, land, landRate, total, profit, margin,
      annualReturn: (margin != null && margin > -1) ? Math.pow(1 + margin, 1 / years) - 1 : null,
      rlv, breakeven, safety: breakeven ? salePpm / breakeven - 1 : null,
      marginStress: stress(0.90, 1.15), marginUpside: stress(1.10, 0.90),
      ownerM2, builderM2, ownerValue, ownerRet, ownerCostEff, ownerRetEff, ownerAnnEff: ann(ownerRetEff),
      ownerCostPerM2: ownerM2 ? ownerCost / ownerM2 : null, builderRev, builderCost, builderMargin,
      builderOk: builderMargin != null && builderMargin >= bTarget,
      ownerFair, ownerRealShare, ownerRealValue, ownerRealRetEff, ownerRealAnnEff: ann(ownerRealRetEff),
      maxBidPartner, maxBidDev: rlv, pv, builderShare: bs, builderTarget: bTarget, ownerTarget: oTarget,
    };
  }

  /** Same rules as report_data.py */
  function verdict(r, vsLandMkt) {
    if (r.builderMargin >= 0.25 && r.ownerRealRetEff >= 0.15) return 'buy';
    if (r.builderMargin >= 0.15 && r.ownerRealRetEff >= 0) return 'thin';
    if ((vsLandMkt || 0) <= -0.15) return 'hold';
    return 'avoid';
  }

  const api = { appraise, verdict, unitSize, hardCost, pvFactor };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Calc = api;
})(typeof window !== 'undefined' ? window : this);
