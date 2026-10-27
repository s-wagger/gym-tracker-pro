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
      timeframeBtns.forEach((b) => b.classList.remove('bg-[#CCFF00]', 'text-black', 'font-black'));
      timeframeBtns.forEach((b) => b.classList.add('bg-gray-800', 'text-gray-300'));
      btn.classList.add('bg-[#CCFF00]', 'text-black', 'font-black');
      btn.classList.remove('bg-gray-800', 'text-gray-300');

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
  const activeBtn = document.querySelector('.btn-timeframe.bg-\\[\\#CCFF00\\]');
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
          borderColor: '#CCFF00',
          backgroundColor: 'rgba(204, 255, 0, 0.08)',
          borderWidth: 3,
          pointBackgroundColor: '#CCFF00',
          pointBorderColor: '#121212',
          pointHoverRadius: 7,
          pointRadius: 4,
          tension: 0.3,
          fill: true
        },
        {
          label: 'Estimated 1RM (Epley)',
          data: oneRMs,
          borderColor: '#FFD700',
          borderDash: [5, 5],
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointBackgroundColor: '#FFD700',
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
            color: '#A0A0A0',
            font: { family: 'sans-serif', size: 12 }
          }
        },
        tooltip: {
          backgroundColor: '#1E1E1E',
          borderColor: '#333333',
          borderWidth: 1,
          titleColor: '#CCFF00',
          bodyColor: '#FFFFFF',
          padding: 12,
          displayColors: true
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#888888', font: { size: 11 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#888888', font: { size: 11 } }
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
            backgroundColor: 'rgba(0, 229, 255, 0.65)',
            hoverBackgroundColor: '#00E5FF',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#1E1E1E',
              borderColor: '#00E5FF',
              borderWidth: 1,
              titleColor: '#00E5FF',
              bodyColor: '#FFF'
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: '#888', font: { size: 10 } }
            },
            y: {
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
              ticks: { color: '#888', font: { size: 10 } }
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
