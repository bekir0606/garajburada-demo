
// admin_panel_live.js - canlı veriyle grafik çizimi

async function fetchDataAndDrawChart() {
  const response = await fetch('/api/admin/stats');
  const stats = await response.json();

  const ctx = document.getElementById('ilanChart').getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: stats.labels,
      datasets: [{
        label: 'İlan Sayısı',
        data: stats.values,
        backgroundColor: ['#3e95cd', '#8e5ea2', '#3cba9f']
      }]
    }
  });
}

document.addEventListener('DOMContentLoaded', fetchDataAndDrawChart);
