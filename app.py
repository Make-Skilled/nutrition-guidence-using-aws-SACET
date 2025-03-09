import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import boto3
from boto3.dynamodb.conditions import Key
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from decimal import Decimal

app = Flask(__name__)
app.secret_key = os.urandom(24)

# AWS DynamoDB configuration
dynamodb = boto3.resource('dynamodb')

# Create DynamoDB tables if they don't exist
def create_tables():
    try:
        # Users table
        users_table = dynamodb.create_table(
            TableName='Users',
            KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("Users table created successfully")
    except Exception as e:
        print(f"Users table might already exist: {str(e)}")

    try:
        # Meal logs table
        meal_logs_table = dynamodb.create_table(
            TableName='MealLogs',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("MealLogs table created successfully")
    except Exception as e:
        print(f"MealLogs table might already exist: {str(e)}")

    try:
        # Meal Plans table
        meal_plans_table = dynamodb.create_table(
            TableName='MealPlans',
            KeySchema=[
                {'AttributeName': 'plan_type', 'KeyType': 'HASH'},
                {'AttributeName': 'day', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'plan_type', 'AttributeType': 'S'},
                {'AttributeName': 'day', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("MealPlans table created successfully")
        # Wait for the table to be created
        meal_plans_table.meta.client.get_waiter('table_exists').wait(TableName='MealPlans')
        print("MealPlans table is now ready")
        return True
    except Exception as e:
        print(f"MealPlans table might already exist: {str(e)}")
        return False

# Initialize meal plans
def initialize_meal_plans():
    meal_plans = {
        'weight_loss': {
            'monday': {
                'breakfast': {
                    'meal': 'Oatmeal with berries and almonds',
                    'calories': 350,
                    'protein': 12,
                    'carbs': 45,
                    'fats': 15
                },
                'lunch': {
                    'meal': 'Grilled chicken salad',
                    'calories': 400,
                    'protein': 35,
                    'carbs': 20,
                    'fats': 22
                },
                'dinner': {
                    'meal': 'Baked salmon with vegetables',
                    'calories': 450,
                    'protein': 30,
                    'carbs': 25,
                    'fats': 28
                }
            },
            'tuesday': {
                'breakfast': {
                    'meal': 'Greek yogurt parfait',
                    'calories': 280,
                    'protein': 15,
                    'carbs': 40,
                    'fats': 8
                },
                'lunch': {
                    'meal': 'Turkey and avocado wrap',
                    'calories': 380,
                    'protein': 25,
                    'carbs': 35,
                    'fats': 18
                },
                'dinner': {
                    'meal': 'Vegetable stir-fry with tofu',
                    'calories': 420,
                    'protein': 25,
                    'carbs': 40,
                    'fats': 15
                }
            },
            'wednesday': {
                'breakfast': {
                    'meal': 'Protein smoothie bowl',
                    'calories': 320,
                    'protein': 20,
                    'carbs': 45,
                    'fats': 10
                },
                'lunch': {
                    'meal': 'Quinoa buddha bowl',
                    'calories': 380,
                    'protein': 22,
                    'carbs': 40,
                    'fats': 16
                },
                'dinner': {
                    'meal': 'Grilled fish with roasted vegetables',
                    'calories': 400,
                    'protein': 35,
                    'carbs': 30,
                    'fats': 18
                }
            },
            'thursday': {
                'breakfast': {
                    'meal': 'Whole grain toast with eggs',
                    'calories': 310,
                    'protein': 18,
                    'carbs': 35,
                    'fats': 14
                },
                'lunch': {
                    'meal': 'Mediterranean salad with chickpeas',
                    'calories': 380,
                    'protein': 20,
                    'carbs': 45,
                    'fats': 16
                },
                'dinner': {
                    'meal': 'Lean turkey meatballs with zucchini noodles',
                    'calories': 420,
                    'protein': 35,
                    'carbs': 25,
                    'fats': 18
                }
            },
            'friday': {
                'breakfast': {
                    'meal': 'Chia seed pudding with fruits',
                    'calories': 290,
                    'protein': 12,
                    'carbs': 42,
                    'fats': 14
                },
                'lunch': {
                    'meal': 'Tuna lettuce wraps',
                    'calories': 350,
                    'protein': 30,
                    'carbs': 15,
                    'fats': 20
                },
                'dinner': {
                    'meal': 'Grilled chicken with sweet potato',
                    'calories': 430,
                    'protein': 35,
                    'carbs': 40,
                    'fats': 15
                }
            },
            'saturday': {
                'breakfast': {
                    'meal': 'Protein pancakes with berries',
                    'calories': 320,
                    'protein': 20,
                    'carbs': 40,
                    'fats': 12
                },
                'lunch': {
                    'meal': 'Lentil soup with whole grain bread',
                    'calories': 380,
                    'protein': 18,
                    'carbs': 50,
                    'fats': 12
                },
                'dinner': {
                    'meal': 'Cod fish with roasted vegetables',
                    'calories': 400,
                    'protein': 35,
                    'carbs': 30,
                    'fats': 15
                }
            },
            'sunday': {
                'breakfast': {
                    'meal': 'Avocado toast with poached eggs',
                    'calories': 340,
                    'protein': 18,
                    'carbs': 35,
                    'fats': 18
                },
                'lunch': {
                    'meal': 'Chicken and quinoa bowl',
                    'calories': 420,
                    'protein': 35,
                    'carbs': 45,
                    'fats': 14
                },
                'dinner': {
                    'meal': 'Grilled shrimp with brown rice',
                    'calories': 380,
                    'protein': 30,
                    'carbs': 40,
                    'fats': 12
                }
            }
        },
        'muscle_gain': {
            'monday': {
                'breakfast': {
                    'meal': 'Protein pancakes with banana',
                    'calories': 500,
                    'protein': 35,
                    'carbs': 60,
                    'fats': 15
                },
                'lunch': {
                    'meal': 'Chicken rice bowl with vegetables',
                    'calories': 650,
                    'protein': 45,
                    'carbs': 70,
                    'fats': 20
                },
                'dinner': {
                    'meal': 'Lean beef stir-fry with noodles',
                    'calories': 700,
                    'protein': 50,
                    'carbs': 65,
                    'fats': 25
                }
            },
            'tuesday': {
                'breakfast': {
                    'meal': 'Egg white omelette with toast',
                    'calories': 450,
                    'protein': 30,
                    'carbs': 45,
                    'fats': 12
                },
                'lunch': {
                    'meal': 'Tuna pasta salad',
                    'calories': 600,
                    'protein': 40,
                    'carbs': 65,
                    'fats': 18
                },
                'dinner': {
                    'meal': 'Grilled chicken with sweet potato',
                    'calories': 680,
                    'protein': 45,
                    'carbs': 70,
                    'fats': 22
                }
            },
            'wednesday': {
                'breakfast': {
                    'meal': 'Protein oatmeal with nuts',
                    'calories': 520,
                    'protein': 32,
                    'carbs': 65,
                    'fats': 18
                },
                'lunch': {
                    'meal': 'Turkey and rice bowl',
                    'calories': 620,
                    'protein': 45,
                    'carbs': 70,
                    'fats': 20
                },
                'dinner': {
                    'meal': 'Salmon with quinoa and vegetables',
                    'calories': 700,
                    'protein': 48,
                    'carbs': 60,
                    'fats': 25
                }
            },
            'thursday': {
                'breakfast': {
                    'meal': 'Protein smoothie with oats',
                    'calories': 550,
                    'protein': 40,
                    'carbs': 70,
                    'fats': 12
                },
                'lunch': {
                    'meal': 'Beef and potato bowl',
                    'calories': 680,
                    'protein': 45,
                    'carbs': 75,
                    'fats': 22
                },
                'dinner': {
                    'meal': 'Chicken pasta with vegetables',
                    'calories': 750,
                    'protein': 50,
                    'carbs': 80,
                    'fats': 20
                }
            },
            'friday': {
                'breakfast': {
                    'meal': 'Greek yogurt with granola and honey',
                    'calories': 520,
                    'protein': 35,
                    'carbs': 65,
                    'fats': 15
                },
                'lunch': {
                    'meal': 'Chicken sandwich with avocado',
                    'calories': 650,
                    'protein': 45,
                    'carbs': 60,
                    'fats': 25
                },
                'dinner': {
                    'meal': 'Steak with baked potato',
                    'calories': 750,
                    'protein': 55,
                    'carbs': 65,
                    'fats': 28
                }
            },
            'saturday': {
                'breakfast': {
                    'meal': 'Protein waffles with fruit',
                    'calories': 580,
                    'protein': 35,
                    'carbs': 75,
                    'fats': 16
                },
                'lunch': {
                    'meal': 'Turkey wrap with cheese',
                    'calories': 620,
                    'protein': 45,
                    'carbs': 65,
                    'fats': 22
                },
                'dinner': {
                    'meal': 'Grilled fish with rice pilaf',
                    'calories': 680,
                    'protein': 50,
                    'carbs': 70,
                    'fats': 20
                }
            },
            'sunday': {
                'breakfast': {
                    'meal': 'Scrambled eggs with toast and bacon',
                    'calories': 600,
                    'protein': 40,
                    'carbs': 50,
                    'fats': 25
                },
                'lunch': {
                    'meal': 'Protein shake with peanut butter sandwich',
                    'calories': 700,
                    'protein': 50,
                    'carbs': 80,
                    'fats': 20
                },
                'dinner': {
                    'meal': 'Grilled chicken breast with pasta',
                    'calories': 720,
                    'protein': 55,
                    'carbs': 75,
                    'fats': 22
                }
            }
        }
    }
        
    try:
        meal_plans_table = dynamodb.Table('MealPlans')
        
        # Delete existing items if any
        scan = meal_plans_table.scan()
        with meal_plans_table.batch_writer() as batch:
            for item in scan['Items']:
                batch.delete_item(
                    Key={
                        'plan_type': item['plan_type'],
                        'day': item['day']
                    }
                )
        
        # Add meal plans for each diet type and day
        for plan_type, days in meal_plans.items():
            for day, meals in days.items():
                meal_plans_table.put_item(
                    Item={
                        'plan_type': plan_type,
                        'day': day,
                        'breakfast': meals['breakfast'],
                        'lunch': meals['lunch'],
                        'dinner': meals['dinner']
                    }
                )
        
        print("Meal plans initialized successfully")
    except Exception as e:
        print(f"Error initializing meal plans: {str(e)}")

def calculate_meal_match(logged_meal, suggested_meal):
    # Calculate match percentage based on nutritional values
    if not logged_meal or not suggested_meal:
        return 0
    
    total_diff = 0
    metrics = ['calories', 'protein', 'carbs', 'fats']
    
    for metric in metrics:
        logged_val = float(logged_meal.get(metric, 0))
        suggested_val = float(suggested_meal.get(metric, 0))
        if suggested_val > 0:
            diff = abs(logged_val - suggested_val) / suggested_val
            total_diff += diff
    
    # Average difference across all metrics
    avg_diff = total_diff / len(metrics)
    match_score = max(0, min(100, (1 - avg_diff) * 100))
    return round(match_score, 1)

# Routes
@app.route('/')
def home():
    if 'user' in session:
        return render_template('dashboard.html')
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        diet_plan = request.form['diet_plan']
        
        users_table = dynamodb.Table('Userdata')
        
        # Check if user already exists
        if users_table.get_item(Key={'email': email}).get('Item'):
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Hash password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Store user with diet plan
        users_table.put_item(Item={
            'email': email,
            'password': hashed_pw.decode('utf-8'),
            'name': name,
            'diet_plan': diet_plan,
            'preferences': {},
            'health_goals': {}
        })
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        users_table = dynamodb.Table('Userdata')
        user = users_table.get_item(Key={'email': email}).get('Item')
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user'] = email
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    users_table = dynamodb.Table('Userdata')
    user = users_table.get_item(Key={'email': session['user']}).get('Item')
    
    if not user:
        return redirect(url_for('login'))

    # Get meal plan for today
    meal_plans_table = dynamodb.Table('MealPlans')
    current_day = datetime.now().strftime('%A').lower()
    meal_plan = None
    
    if user.get('diet_plan'):
        try:
            scan_response = meal_plans_table.scan()
            all_plans = scan_response.get('Items', [])
            
            # Find the matching meal plan
            for plan in all_plans:
                if (plan.get('plan_type', '').lower() == user['diet_plan'].lower() and 
                    plan.get('day', '').lower() == current_day):
                    # Format meal plan data
                    meal_plan = {
                        'breakfast_name': plan.get('breakfast', {}).get('meal', ''),
                        'breakfast_calories': plan.get('breakfast', {}).get('calories', 0),
                        'breakfast_protein': plan.get('breakfast', {}).get('protein', 0),
                        'breakfast_carbs': plan.get('breakfast', {}).get('carbs', 0),
                        'breakfast_fats': plan.get('breakfast', {}).get('fats', 0),
                        
                        'lunch_name': plan.get('lunch', {}).get('meal', ''),
                        'lunch_calories': plan.get('lunch', {}).get('calories', 0),
                        'lunch_protein': plan.get('lunch', {}).get('protein', 0),
                        'lunch_carbs': plan.get('lunch', {}).get('carbs', 0),
                        'lunch_fats': plan.get('lunch', {}).get('fats', 0),
                        
                        'dinner_name': plan.get('dinner', {}).get('meal', ''),
                        'dinner_calories': plan.get('dinner', {}).get('calories', 0),
                        'dinner_protein': plan.get('dinner', {}).get('protein', 0),
                        'dinner_carbs': plan.get('dinner', {}).get('carbs', 0),
                        'dinner_fats': plan.get('dinner', {}).get('fats', 0)
                    }
                    break
        except Exception as e:
            print(f"Error fetching meal plan: {str(e)}")

    # Get today's meal logs
    meal_logs_table = dynamodb.Table('MealLogs')
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        response = meal_logs_table.query(
            KeyConditionExpression=Key('user_id').eq(session['user']) & 
                                 Key('timestamp').begins_with(today)
        )
        recent_meals = response.get('Items', [])
        
        # Sort meals by timestamp in descending order
        recent_meals.sort(key=lambda x: x['timestamp'], reverse=True)
    except Exception as e:
        print(f"Error fetching meal logs: {str(e)}")
        recent_meals = []

    # Calculate weekly progress
    weekly_progress = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        try:
            response = meal_logs_table.query(
                KeyConditionExpression=Key('user_id').eq(session['user']) & 
                                     Key('timestamp').begins_with(date)
            )
            day_meals = response.get('Items', [])
            avg_score = sum(float(meal.get('match_score', 0)) for meal in day_meals) / len(day_meals) if day_meals else 0
            weekly_progress.append({
                'date': date,
                'score': round(avg_score, 1)
            })
        except Exception as e:
            print(f"Error calculating weekly progress: {str(e)}")
            weekly_progress.append({
                'date': date,
                'score': 0
            })

    weekly_progress.reverse()  # Show oldest to newest

    return render_template('dashboard.html', 
                         user=user,
                         meal_plan=meal_plan,
                         current_day=current_day,
                         recent_meals=recent_meals,
                         weekly_progress=weekly_progress)

@app.route('/log-meal', methods=['POST'])
def log_meal():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        meal_type = request.form.get('meal_type')
        food = request.form.get('food')
        calories = Decimal(str(request.form.get('calories')))
        protein = Decimal(str(request.form.get('protein')))
        carbs = Decimal(str(request.form.get('carbs')))
        fats = Decimal(str(request.form.get('fats')))

        # Get user's meal plan
        meal_plans_table = dynamodb.Table('MealPlans')
        users_table = dynamodb.Table('Userdata')
        user = users_table.get_item(Key={'email': session['user']}).get('Item')
        
        current_day = datetime.now().strftime('%A').lower()
        meal_plan = None
        match_score = Decimal('0')
        
        if user and user.get('diet_plan'):
            try:
                scan_response = meal_plans_table.scan()
                all_plans = scan_response.get('Items', [])
                
                # Find the matching meal plan
                for plan in all_plans:
                    if (plan.get('plan_type', '').lower() == user['diet_plan'].lower() and 
                        plan.get('day', '').lower() == current_day):
                        meal_plan = plan
                        break

                if meal_plan:
                    # Get suggested values for the meal type
                    suggested_meal = meal_plan.get(meal_type, {})
                    suggested_values = {
                        'calories': Decimal(str(suggested_meal.get('calories', 0))),
                        'protein': Decimal(str(suggested_meal.get('protein', 0))),
                        'carbs': Decimal(str(suggested_meal.get('carbs', 0))),
                        'fats': Decimal(str(suggested_meal.get('fats', 0)))
                    }

                    # Calculate match score
                    scores = []
                    if suggested_values['calories'] > 0:
                        cal_score = Decimal('100') - min(Decimal('100'), abs(calories - suggested_values['calories']) / suggested_values['calories'] * Decimal('100'))
                        scores.append(cal_score)
                    if suggested_values['protein'] > 0:
                        protein_score = Decimal('100') - min(Decimal('100'), abs(protein - suggested_values['protein']) / suggested_values['protein'] * Decimal('100'))
                        scores.append(protein_score)
                    if suggested_values['carbs'] > 0:
                        carbs_score = Decimal('100') - min(Decimal('100'), abs(carbs - suggested_values['carbs']) / suggested_values['carbs'] * Decimal('100'))
                        scores.append(carbs_score)
                    if suggested_values['fats'] > 0:
                        fats_score = Decimal('100') - min(Decimal('100'), abs(fats - suggested_values['fats']) / suggested_values['fats'] * Decimal('100'))
                        scores.append(fats_score)
                    
                    match_score = round(sum(scores) / Decimal(str(len(scores))), 1) if scores else Decimal('0')

            except Exception as e:
                print(f"Error calculating match score: {str(e)}")

        # Create meal log entry
        meal_logs_table = dynamodb.Table('MealLogs')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        meal_log = {
            'user_id': session['user'],
            'timestamp': timestamp,
            'meal_type': meal_type,
            'food': food,
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fats': fats,
            'match_score': match_score
        }
        
        meal_logs_table.put_item(Item=meal_log)
        return jsonify({'success': True}), 200

    except Exception as e:
        print(f"Error logging meal: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-todays-meals')
def get_todays_meals():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        meal_logs_table = dynamodb.Table('MealLogs')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Query meals logged today for the current user
        response = meal_logs_table.query(
            KeyConditionExpression=Key('user_id').eq(session['user']) & 
                                 Key('timestamp').begins_with(today)
        )
        
        meals = response.get('Items', [])
        
        # Convert Decimal to float for JSON serialization
        for meal in meals:
            meal['calories'] = float(meal['calories'])
            meal['protein'] = float(meal['protein'])
            meal['carbs'] = float(meal['carbs'])
            meal['fats'] = float(meal['fats'])
            meal['match_score'] = float(meal['match_score'])
        
        # Sort meals by timestamp
        meals.sort(key=lambda x: x['timestamp'])
        
        return jsonify({
            'success': True,
            'meals': meals
        })
    except Exception as e:
        print(f"Error fetching today's meals: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    create_tables()
    print("Reinitializing meal plans...")
    initialize_meal_plans()
    app.run(debug=True,host='0.0.0.0',port=5000)