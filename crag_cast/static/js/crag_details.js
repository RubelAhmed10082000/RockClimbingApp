        function getBadgeClass(metricName, value){
            if (value === null || value === undefined) return 'badge-default';

            switch (metricName) {
                case 'temperature':
                    if (value < 10) return 'badge-bad';
                    else if (value >= 10 && value <= 15) return 'badge-mild';
                    else if (value > 15 && value <= 25) return 'badge-good';
                    else if (value > 25 && value <= 30) return 'badge-mild';
                    else if (value > 30) return 'badge-bad';
                    else return 'badge-bad';

                case 'humidity':
                    if (value > 70) return 'badge-bad';
                    else if (value <= 70 && value > 50) return 'badge-mild';
                    else if (value < 50) return 'badge-good';

                case 'precipitation':
                    if (value === 0 ) return 'badge-good';
                    else return 'badge-bad';

                case 'windspeed':
                    if (value <= 20) return 'badge-good';
                    else if (value > 20 && value < 30) return 'badge-mild';
                    else return 'badge-bad'
                
                default: 
                    return 'badge-default'
            }
        }

        const routesList = document.getElementById('routesList');
        
        if (routesList) {
            const routeItems = Array.from(routesList.getElementsByClassName('route-item'));
            const prevPageBtn = document.getElementById('prevPage');
            const nextPageBtn = document.getElementById('nextPage');
            const currentPageSpan = document.getElementById('currentPage');
            const totalPagesSpan = document.getElementById('totalPages');
            const routesPerPageSelect = document.getElementById('routesPerPage');
            const routeSearch = document.getElementById('routeSearch');

            let currentPage = 1;
            let routesPerPage = parseInt(routesPerPageSelect.value);
            let filteredRoutes = routeItems;

            function updatePagination() {
                const totalPages = Math.ceil(filteredRoutes.length / routesPerPage);
                currentPage = Math.min(currentPage, totalPages);
                
                prevPageBtn.disabled = currentPage === 1;
                nextPageBtn.disabled = currentPage === totalPages;
                currentPageSpan.textContent = currentPage;
                totalPagesSpan.textContent = totalPages;

                routeItems.forEach(function(item) {
                    item.classList.add('hidden');
                });
                const start = (currentPage - 1) * routesPerPage;
                const end = start + routesPerPage;
                filteredRoutes.slice(start, end).forEach(function(item) {
                    item.classList.remove('hidden');
                });
            }}
            

            function filterRoutes() {
                const searchTerm = routeSearch.value.toLowerCase();
                filteredRoutes = routeItems.filter(item => {
                    const routeName = item.querySelector('.route-name').textContent.toLowerCase();
                    const routeType = item.querySelector('.route-type')?.textContent.toLowerCase() || '';
                    const routeGrade = item.querySelector('.route-grade').textContent.toLowerCase();
                    return routeName.includes(searchTerm) || 
                           routeType.includes(searchTerm) || 
                           routeGrade.includes(searchTerm);
                });
                currentPage = 1;
                updatePagination();
            }

            prevPageBtn.addEventListener('click', () => {
                if (currentPage > 1) {
                    currentPage--;
                    updatePagination();
                }
            });

            nextPageBtn.addEventListener('click', () => {
                const totalPages = Math.ceil(filteredRoutes.length / routesPerPage);
                if (currentPage < totalPages) {
                    currentPage++;
                    updatePagination();
                }
            });

            routesPerPageSelect.addEventListener('change', () => {
                routesPerPage = parseInt(routesPerPageSelect.value);
                currentPage = 1;
                updatePagination();
            });

            routeSearch.addEventListener('input', filterRoutes);

            updatePagination();

        const map = L.map('map').setView([{{ crag.crag_latitude }}, {{ crag.crag_longitude }}], 13);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        L.marker([{{ crag.crag_latitude }}, {{ crag.crag_longitude }}])
            .addTo(map)
            .bindPopup('{{ crag.name }}');

    
    async function loadWeather() {
    try {
        const response = await fetch(`/api/forecast/{{ crag.crag_latitude }}/{{ crag.crag_longitude }}`);
        const data = await response.json();
        if (!data.forecast) throw new Error("No forecast data");

        const container = document.getElementById("weatherForecast");

        const scrollContainer = document.createElement('div');
        scrollContainer.style.overflowX = 'scroll';
        scrollContainer.style.width = 'max-content';
        scrollContainer.style.height = 'max-content';
        scrollContainer.style.display = 'block';
        scrollContainer.style.marginTop = '1rem';

        const table = document.createElement('table');
        table.style.width = 'max-content';
        table.style.borderCollapse = 'collapse';
        table.style.tableLayout = 'auto';
        table.style.fontSize = '0.875rem';

       const timestamps = data.forecast.map(entry => {
        const date = new Date(entry.time);
        return date.toLocaleString('en-GB', {
            day: '2-digit',
            month: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    });

        function buildRow(label, values, unit) {
            return `<tr>
                <td style="padding: 0.5rem; font-weight: 600; white-space: nowrap;">${label}</td>
                ${values.map(v => {
                    const cls = getBadgeClass(label.toLowerCase().split(' ')[0], parseFloat(v));
                    return `<td style="padding: 0.5rem; white-space: nowrap; text-align: center;" class="badge ${cls}">${v}${unit}</td>`;
                }).join('')}
            </tr>`;
        }

        table.innerHTML = `
            <thead>
                <tr>
                    <th style="text-align:left; padding: 0.5rem;">Metric</th>
                    ${timestamps.map(t => `<th style="padding: 0.5rem; white-space: nowrap; ">${t}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${buildRow('Temperature (℃)', data.forecast.map(e => e.temperature), '℃')}
                ${buildRow('Humidity (%)', data.forecast.map(e => e.humidity), '%')}
                ${buildRow('Precipitation (mm)', data.forecast.map(e => e.precipitation), 'mm')}
                ${buildRow('Windspeed (km/h)', data.forecast.map(e => e.windspeed), 'km/h')}
            </tbody>
        `;

        scrollContainer.appendChild(table);
        container.innerHTML = '';
        container.appendChild(scrollContainer);

    } catch (error) {
        console.error("Error loading weather data:", error);
        const container = document.getElementById("weatherForecast");
        container.innerText = "Unable to load forecast data.";
    }
}

loadWeather();

