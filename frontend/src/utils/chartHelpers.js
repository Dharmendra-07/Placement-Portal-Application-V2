/**
 * utils/chartHelpers.js
 * Reusable Chart.js factory functions used across all analytics views.
 */
import {
  Chart, LineController, BarController, DoughnutController,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Tooltip, Legend, Filler,
} from 'chart.js'

Chart.register(
  LineController, BarController, DoughnutController,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Tooltip, Legend, Filler,
)

const PALETTE = [
  '#0d6efd','#198754','#fd7e14','#dc3545',
  '#6f42c1','#0dcaf0','#ffc107','#20c997',
]

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,3),16)
  const g = parseInt(hex.slice(3,5),16)
  const b = parseInt(hex.slice(5,7),16)
  return `rgba(${r},${g},${b},${alpha})`
}

export function buildTrendLine(canvas, labels, datasets) {
  if (!canvas) return null
  return new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: datasets.map((ds, i) => ({
        label:           ds.label,
        data:            ds.data,
        borderColor:     ds.color || PALETTE[i],
        backgroundColor: hexToRgba(ds.color || PALETTE[i], 0.08),
        tension:         0.4,
        fill:            true,
        pointRadius:     4,
      })),
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'top' } },
      scales:  { y: { beginAtZero: true } },
    },
  })
}

export function buildDoughnut(canvas, labels, data) {
  if (!canvas) return null
  return new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: PALETTE.slice(0, data.length),
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } },
      cutout: '60%',
    },
  })
}

export function buildBar(canvas, labels, data, label='', color='#0d6efd') {
  if (!canvas) return null
  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: hexToRgba(color, 0.8),
        borderColor:     color,
        borderWidth:     1,
        borderRadius:    6,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: !!label } },
      scales:  { y: { beginAtZero: true } },
    },
  })
}

export function buildHorizontalBar(canvas, labels, data, label='', color='#0d6efd') {
  if (!canvas) return null
  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: hexToRgba(color, 0.8),
        borderRadius: 4,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: { legend: { display: false } },
      scales:  { x: { beginAtZero: true } },
    },
  })
}

export function buildGroupedBar(canvas, labels, datasets) {
  if (!canvas) return null
  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: datasets.map((ds, i) => ({
        label:           ds.label,
        data:            ds.data,
        backgroundColor: hexToRgba(ds.color || PALETTE[i], 0.8),
        borderRadius:    4,
      })),
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'top' } },
      scales:  { y: { beginAtZero: true } },
    },
  })
}
