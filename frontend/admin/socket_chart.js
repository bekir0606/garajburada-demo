
const socket = io();

socket.on('grafikData', (stats) => {
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
});
