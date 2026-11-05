/**
 * Gym Tracker Pro - PR Analytics & Milestones
 * Renders Chart.js weight and volume progression curves,
 * updates milestone achievements, and manages exercise filtering.
 */

let progressChart = null;
let volumeChart = null;

function initAnalytics() {
  const exerciseSelect = document.getElementById('analytics-exercise-select');
  const timeframeBtns = document.querySelectorAll('.btn-timeframe');

  if (exerciseSelect) {
    exerciseSelect.addEventListener('change', () => {
      loadProgressionData(exerciseSelect.value, getSelectedTimeframe());
    });
  }

  timeframeBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      timeframeBtns.forEach((b) => b.classList.remove('bg-[#2563EB]', 'text-white', 'font-black'));
      timeframeBtns.forEach((b) => b.classList.add('bg-[#16254F]', 'text-gray-300', 'font-semibold'));
      btn.classList.add('bg-[#2563EB]', 'text-white', 'font-black');
      btn.classList.remove('bg-[#16254F]', 'text-gray-300', 'font-semibold');

      if (exerciseSelect) {
        loadProgressionData(exerciseSelect.value, parseInt(btn.dataset.days || 0));
      }
    });
  });

  // Load initial progression chart
  if (exerciseSelect && exerciseSelect.value) {
    loadProgressionData(exerciseSelect.value, 90);
  }

  // Load volume history chart
  loadVolumeChartData();
}

function getSelectedTimeframe() {
  const activeBtn = document.querySelector('.btn-timeframe.bg-\\[\\#2563EB\\]');
  return activeBtn ? parseInt(activeBtn.dataset.days || 0) : 90;
}

async function loadProgressionData(exercise, days) {
  try {
    const params = new URLSearchParams({ exercise: exercise });
    if (days > 0) params.append('days', days);

    const res = await fetch(`/api/analytics/progression?${params.toString()}`);
    const data = await res.json();

    if (res.ok && data.points) {
      renderProgressChart(exercise, data.points);
    }
  } catch (err) {
    console.error('Error fetching progression data:', err);
  }
}

function renderProgressChart(exercise, points) {
  const ctx = document.getElementById('chart-progression');
  if (!ctx) return;

  const labels = points.map((p) => p.date);
  const weights = points.map((p) => p.weight);
  const oneRMs = points.map((p) => p.estimated_1rm);

  if (progressChart) {
    progressChart.destroy();
  }

  if (points.length === 0) {
    // Show empty placeholder
    const chartCard = document.getElementById('chart-container-box');
    if (chartCard) {
      // Don't wipe canvas, just create zero state
    }
  }

  progressChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: `${exercise} Max Weight`,
          data: weights,
          borderColor: '#2563EB',
          backgroundColor: 'rgba(37, 99, 235, 0.15)',
          borderWidth: 3,
          pointBackgroundColor: '#2563EB',
          pointBorderColor: '#0A1128',
          pointHoverRadius: 7,
          pointRadius: 4,
          tension: 0.3,
          fill: true
        },
        {
          label: 'Estimated 1RM (Epley)',
          data: oneRMs,
          borderColor: '#E6D5B8',
          borderDash: [5, 5],
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointBackgroundColor: '#E6D5B8',
          pointRadius: 3,
          tension: 0.2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          labels: {
            color: '#E6D5B8',
            font: { family: 'sans-serif', size: 12 }
          }
        },
        tooltip: {
          backgroundColor: '#101C3D',
          borderColor: '#2563EB',
          borderWidth: 1,
          titleColor: '#E6D5B8',
          bodyColor: '#FFFFFF',
          padding: 12,
          displayColors: true
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(37, 99, 235, 0.1)' },
          ticks: { color: '#8892B0', font: { size: 11 } }
        },
        y: {
          grid: { color: 'rgba(37, 99, 235, 0.1)' },
          ticks: { color: '#8892B0', font: { size: 11 } }
        }
      }
    }
  });
}

async function loadVolumeChartData() {
  const ctx = document.getElementById('chart-volume');
  if (!ctx) return;

  try {
    const res = await fetch('/api/analytics/volume-history');
    const data = await res.json();
    if (res.ok && data.sessions) {
      const labels = data.sessions.map((s) => s.date);
      const volumes = data.sessions.map((s) => s.total_volume);

      if (volumeChart) volumeChart.destroy();

      volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Total Volume Lifted',
            data: volumes,
            backgroundColor: 'rgba(37, 99, 235, 0.75)',
            hoverBackgroundColor: '#2563EB',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#101C3D',
              borderColor: '#2563EB',
              borderWidth: 1,
              titleColor: '#E6D5B8',
              bodyColor: '#FFF'
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: '#8892B0', font: { size: 10 } }
            },
            y: {
              grid: { color: 'rgba(37, 99, 235, 0.1)' },
              ticks: { color: '#8892B0', font: { size: 10 } }
            }
          }
        }
      });
    }
  } catch (err) {
    console.error('Error fetching volume history:', err);
  }
}

document.addEventListener('DOMContentLoaded', initAnalytics);
