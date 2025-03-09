document.addEventListener('DOMContentLoaded', function() {
    // Handle meal form submission
    const mealForm = document.getElementById('meal-form');
    if (mealForm) {
        mealForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const mealData = {
                meal_type: document.getElementById('meal-type').value,
                calories: parseInt(document.getElementById('calories').value),
                foods: document.getElementById('foods').value.split(',').map(food => food.trim()),
                macros: {
                    protein: parseInt(document.getElementById('protein').value),
                    carbs: parseInt(document.getElementById('carbs').value),
                    fats: parseInt(document.getElementById('fats').value)
                }
            };

            try {
                const response = await fetch('/log-meal', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(mealData)
                });

                if (response.ok) {
                    // Reload page to show updated meal list
                    window.location.reload();
                } else {
                    throw new Error('Failed to log meal');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to log meal. Please try again.');
            }
        });
    }

    // Update macronutrient totals
    function updateMacroTotals() {
        const meals = document.querySelectorAll('#recent-meals tr');
        let totalCalories = 0;
        let totalProtein = 0;
        let totalCarbs = 0;
        let totalFats = 0;

        meals.forEach(meal => {
            const calories = parseInt(meal.children[3].textContent);
            const macros = meal.children[4].textContent.split('\n');
            
            totalCalories += calories;
            totalProtein += parseInt(macros[0].split(':')[1]);
            totalCarbs += parseInt(macros[1].split(':')[1]);
            totalFats += parseInt(macros[2].split(':')[1]);
        });

        // Update the totals in the UI if elements exist
        const totalsElement = document.getElementById('macro-totals');
        if (totalsElement) {
            totalsElement.innerHTML = `
                <strong>Daily Totals:</strong><br>
                Calories: ${totalCalories}<br>
                Protein: ${totalProtein}g<br>
                Carbs: ${totalCarbs}g<br>
                Fats: ${totalFats}g
            `;
        }
    }

    // Call updateMacroTotals when page loads if we're on the dashboard
    if (document.getElementById('recent-meals')) {
        updateMacroTotals();
    }

    // Chart configurations
    let weeklyProgressChart = null;
    let macroComparisonChart = null;
    let calorieComparisonChart = null;

    // Initialize charts when document is ready
    initializeCharts();
    if (mealPlanData) {
        compareMealsWithPlan();
    }

    function initializeCharts() {
        // Weekly Progress Chart
        const weeklyCtx = document.getElementById('weeklyProgressChart').getContext('2d');
        weeklyProgressChart = new Chart(weeklyCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Meal Plan Adherence',
                    data: [0, 0, 0, 0, 0, 0, 0],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Adherence %'
                        }
                    }
                }
            }
        });

        // Macro Comparison Chart
        const macroCtx = document.getElementById('macroComparisonChart').getContext('2d');
        macroComparisonChart = new Chart(macroCtx, {
            type: 'bar',
            data: {
                labels: ['Protein', 'Carbs', 'Fats'],
                datasets: [
                    {
                        label: 'Suggested',
                        data: [0, 0, 0],
                        backgroundColor: 'rgba(75, 192, 192, 0.5)'
                    },
                    {
                        label: 'Actual',
                        data: [0, 0, 0],
                        backgroundColor: 'rgba(255, 99, 132, 0.5)'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Grams'
                        }
                    }
                }
            }
        });

        // Calorie Comparison Chart
        const calorieCtx = document.getElementById('calorieComparisonChart').getContext('2d');
        calorieComparisonChart = new Chart(calorieCtx, {
            type: 'doughnut',
            data: {
                labels: ['Consumed', 'Remaining'],
                datasets: [{
                    data: [0, 2000],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(255, 99, 132, 0.5)'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Daily Calorie Goal'
                    }
                }
            }
        });
    }

    function compareMealsWithPlan() {
        const recentMeals = document.querySelectorAll('#recent-meals tr');
        let matchedMeals = 0;
        let totalMeals = 0;

        recentMeals.forEach((meal, index) => {
            const mealType = meal.children[1].textContent.toLowerCase();
            const foods = meal.children[2].textContent;
            const calories = parseInt(meal.children[3].textContent);
            const macros = parseMacros(meal.children[4].textContent);
            const matchStatusCell = document.getElementById(`match-status-${index + 1}`);

            if (mealPlanData && mealPlanData[mealType]) {
                const plannedMeal = mealPlanData[mealType];
                const calorieMatch = Math.abs(calories - plannedMeal.calories) <= 50;
                const macroMatch = compareMacros(macros, plannedMeal);
                
                if (calorieMatch && macroMatch) {
                    matchStatusCell.innerHTML = '<span class="badge bg-success">Perfect Match</span>';
                    matchedMeals++;
                } else if (calorieMatch || macroMatch) {
                    matchStatusCell.innerHTML = '<span class="badge bg-warning">Partial Match</span>';
                    matchedMeals += 0.5;
                } else {
                    matchStatusCell.innerHTML = '<span class="badge bg-danger">No Match</span>';
                }
                totalMeals++;
            }
        });

        // Update progress indicators
        const adherenceRate = totalMeals > 0 ? (matchedMeals / totalMeals) * 100 : 0;
        document.getElementById('mealsMatchedCount').textContent = matchedMeals.toFixed(1);
        document.getElementById('adherenceRate').textContent = adherenceRate.toFixed(1) + '%';

        // Update charts
        updateCharts(matchedMeals, totalMeals);
    }

    function parseMacros(macroText) {
        const protein = parseInt(macroText.match(/P: (\d+)g/)[1]);
        const carbs = parseInt(macroText.match(/C: (\d+)g/)[1]);
        const fats = parseInt(macroText.match(/F: (\d+)g/)[1]);
        return { protein, carbs, fats };
    }

    function compareMacros(actual, planned) {
        const tolerance = 5; // 5g tolerance for macros
        return Math.abs(actual.protein - planned.protein) <= tolerance &&
               Math.abs(actual.carbs - planned.carbs) <= tolerance &&
               Math.abs(actual.fats - planned.fats) <= tolerance;
    }

    function updateCharts(matchedMeals, totalMeals) {
        // Update weekly progress chart
        const dayIndex = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
            .indexOf(currentDay.toLowerCase());
        
        const progressData = weeklyProgressChart.data.datasets[0].data;
        progressData[dayIndex] = totalMeals > 0 ? (matchedMeals / totalMeals) * 100 : 0;
        weeklyProgressChart.update();

        // Update macro comparison chart
        if (mealPlanData) {
            const suggestedMacros = {
                protein: 0,
                carbs: 0,
                fats: 0
            };
            
            Object.values(mealPlanData).forEach(meal => {
                suggestedMacros.protein += meal.protein;
                suggestedMacros.carbs += meal.carbs;
                suggestedMacros.fats += meal.fats;
            });

            const actualMacros = {
                protein: 0,
                carbs: 0,
                fats: 0
            };

            document.querySelectorAll('#recent-meals tr').forEach(meal => {
                const macros = parseMacros(meal.children[4].textContent);
                actualMacros.protein += macros.protein;
                actualMacros.carbs += macros.carbs;
                actualMacros.fats += macros.fats;
            });

            macroComparisonChart.data.datasets[0].data = [
                suggestedMacros.protein,
                suggestedMacros.carbs,
                suggestedMacros.fats
            ];
            macroComparisonChart.data.datasets[1].data = [
                actualMacros.protein,
                actualMacros.carbs,
                actualMacros.fats
            ];
            macroComparisonChart.update();

            // Update calorie comparison chart
            const totalCalories = Object.values(mealPlanData)
                .reduce((sum, meal) => sum + meal.calories, 0);
            const consumedCalories = Array.from(document.querySelectorAll('#recent-meals tr'))
                .reduce((sum, meal) => sum + parseInt(meal.children[3].textContent), 0);

            calorieComparisonChart.data.datasets[0].data = [
                consumedCalories,
                Math.max(0, totalCalories - consumedCalories)
            ];
            calorieComparisonChart.update();
        }
    }

    // Handle week switching
    function showWeek(weekNumber) {
        // This function will be implemented when we add week 2 meal plans
        fetch(`/get_meal_plan?week=${weekNumber}`)
            .then(response => response.json())
            .then(data => {
                if (data.meal_plan) {
                    updateMealPlanDisplay(data.meal_plan);
                }
            })
            .catch(error => console.error('Error fetching meal plan:', error));
    }

    function updateMealPlanDisplay(mealPlan) {
        // Update the meal plan cards with new data
        if (mealPlan.breakfast) {
            updateMealCard('breakfast', mealPlan.breakfast);
        }
        if (mealPlan.lunch) {
            updateMealCard('lunch', mealPlan.lunch);
        }
        if (mealPlan.dinner) {
            updateMealCard('dinner', mealPlan.dinner);
        }
    }

    function updateMealCard(mealType, mealData) {
        const card = document.querySelector(`[data-meal-type="${mealType}"]`);
        if (card) {
            card.querySelector('.meal-name').textContent = mealData.meal;
            card.querySelector('.calories').textContent = `Calories: ${mealData.calories}`;
            card.querySelector('.macros').innerHTML = `
                Protein: ${mealData.protein}g<br>
                Carbs: ${mealData.carbs}g<br>
                Fats: ${mealData.fats}g
            `;
        }
    }
});
