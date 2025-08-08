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

        async function fetchWeather(lat, lon, row) {
            const weatherCell = row.querySelector('.weather-data');
            try {
                const response = await fetch(`/api/weather/${lat}/${lon}`);
                const weather = await response.json();
                if (weather.error) throw Error(weather.error);
                
                const tClass = getBadgeClass('temperature', weather.temperature);
                const hClass = getBadgeClass('humidity', weather.humidity);
                const pClass = getBadgeClass('precipitation', weather.precipitation);
                const wClass = getBadgeClass('windspeed', weather.windspeed);



                weatherCell.innerHTML = `

                        <div class="weather-metric">
                            <div class="metric-label">Temperature(C)</div>
                            <span class="badge ${tClass}">${weather.temperature ?? 'N/A'}°C</span>
                        </div>

                        <div class="weather-metric">
                            <div class="metric-label">Humidity(%)</div>
                            <span class="badge ${hClass}">${weather.humidity ?? 'N/A'}%</span>
                        </div>

                        <div class="weather-metric">
                            <div class="metric-label">Precipitation(mm)</div>
                            <span class="badge ${pClass}">${weather.precipitation ?? 'N/A'} mm</span>
                        </div>

                        <div class="weather-metric">
                            <div class="metric-label">Windspeed(Km/h)</div>
                            <span class="badge ${wClass}">${weather.windspeed ?? 'N/A'} Km/h</span>
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Error fetching weather:', error);
                weatherCell.innerHTML = '<div class="weather-cell">Weather data unavailable</div>';
            }
        }

        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const row = entry.target;
                    const lat = row.dataset.lat;
                    const lon = row.dataset.lon;
                    if (row.querySelector('.weather-loading')) {
                        fetchWeather(lat, lon, row);
                    }
                    observer.unobserve(row);
                }
            });
        }, {
            root: null,
            rootMargin: '50px',
            threshold: 0.1
        });

        document.querySelectorAll('tr[data-lat][data-lon]').forEach(row => {
            if (row.querySelector('.weather-loading')) {
                observer.observe(row);
            }
        });


        window.addEventListener('unload', () => observer.disconnect());


        function clearFilter(filterName, filterValue = null) {
            const form = document.getElementById('searchForm');
            const selectElement = form.querySelector(`select[name="${filterName}"]`);
            if (selectElement) {
                const options = Array.from(selectElement.options);
                options.forEach(option => {
                    if (!filterValue || option.value == filterValue) {
                        option.selected = false;
                    }
                })
            }
            form.submit();
        }

        document.querySelectorAll('.filter-group select').forEach(select => {
            select.addEventListener('change', () => {
                document.getElementById('searchForm').submit();
            });
        });

        document.querySelectorAll('.sort-header').forEach(header => {
            header.addEventListener('click', () => {
                const sortBy = header.dataset.sort;
                const currentSortBy = document.getElementById('sortBy').value;
                const currentSortOrder = document.getElementById('sortOrder').value;
                
                const newSortOrder = (sortBy === currentSortBy && currentSortOrder === 'asc') ? 'desc' : 'asc';
                
                document.getElementById('sortBy').value = sortBy;
                document.getElementById('sortOrder').value = newSortOrder;
                document.getElementById('searchForm').submit();
            });
        });

    document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('searchForm');
    const selects = form.querySelectorAll('select');

    selects.forEach(select => {
        new Choices(select, {
            removeItemButton: true,
            shouldSort: false,
            placeholderValue: select.getAttribute('placeholder') || 'Select options',
            searchPlaceholderValue: 'Search...',
            classNames: {
                containerInner: 'choices__inner',
                input: 'choices__input',
                selectedState: 'choices__selected',
                item: 'choices__item',
                choice: 'choices__choice',
                disabledState: 'choices__disabled',
                highlightedState: 'choices__highlighted',
                itemSelectable: 'choices__item--selectable',
                button: 'choices__button',
                group: 'choices__group',
                placeholder: 'choices__placeholder'
            },
            callbackOnCreateTemplates: function (template) {
                return {
                    choice: (classNames, data) => {
                        return template(`
                            <div class="${classNames.item} ${classNames.itemChoice} ${data.disabled ? classNames.itemDisabled : ''}" data-select-text="" data-choice ${data.disabled ? 'data-choice-disabled aria-disabled="true"' : 'data-choice-selectable'} data-id="${data.id}" data-value="${data.value}" ${data.groupId > 0 ? 'role="treeitem"' : 'role="option"'}>
                                <input type="checkbox" class="choices__checkbox" ${data.selected ? 'checked' : ''} tabindex="-1" />
                                <span>${data.label}</span>
                            </div>
                        `);
                    }
                };
            }
        });

        select.addEventListener('change', () => {
            form.submit();
        });
    });
});
