
// admin_panel.js - grafik ve push mock örnek
const ctx = document.getElementById('ilanChart').getContext('2d');
const ilanChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Otomobil', 'Ticari', 'SUV'],
    datasets: [{
      label: 'İlan Sayısı',
      data: [24, 12, 8],
      backgroundColor: ['#3e95cd', '#8e5ea2', '#3cba9f']
    }]
  }
});

// Push bildirimi örneği (simülasyon)
function showPushNotification(message) {
  alert("🔔 PUSH BİLDİRİM: " + message);
}
