from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_client_data(clientname):
    filename = f'data/{clientname}.json'
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {'items': [], 'categories': []}

def save_client_data(clientname, data):
    with open(f'data/{clientname}.json', 'w') as f:
        json.dump(data, f, indent=2)

def get_clients():
    if os.path.exists('data/clients.json'):
        with open('data/clients.json', 'r') as f:
            return json.load(f)
    return {}

@app.route('/<clientname>/menu')
def show_menu(clientname):
    menu_data = get_client_data(clientname)
    return render_template('menu.html', menu=menu_data, clientname=clientname)

@app.route('/<clientname>/<token>/edit', methods=['GET', 'POST'])
def edit_menu(clientname, token):
    # Verify token
    clients = get_clients()
    if clientname not in clients or clients[clientname] != token:
        flash('Invalid access', 'danger')
        return redirect(url_for('index'))
    
    menu_data = get_client_data(clientname)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_item':
            # Handle file upload
            image_file = request.files.get('image')
            image_filename = None
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_filename = f"{clientname}_{filename}"
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            
            new_item = {
                'id': len(menu_data['items']) + 1,
                'name': request.form['name'],
                'ingredients': request.form['ingredients'],
                'price': float(request.form['price']),
                'category': request.form['category'],
                'image': image_filename
            }
            menu_data['items'].append(new_item)
            
            # Add to categories if new
            if new_item['category'] not in menu_data['categories']:
                menu_data['categories'].append(new_item['category'])
            
            flash('Item added successfully', 'success')
        
        elif action == 'update_item':
            item_id = int(request.form['item_id'])
            for item in menu_data['items']:
                if item['id'] == item_id:
                    item['name'] = request.form['name']
                    item['ingredients'] = request.form['ingredients']
                    item['price'] = float(request.form['price'])
                    item['category'] = request.form['category']
                    
                    # Handle image update
                    image_file = request.files.get('image')
                    if image_file and allowed_file(image_file.filename):
                        # Delete old image if exists
                        if item['image']:
                            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item['image'])
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                        
                        # Save new image
                        filename = secure_filename(image_file.filename)
                        image_filename = f"{clientname}_{filename}"
                        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                        item['image'] = image_filename
                    
                    flash('Item updated successfully', 'success')
                    break
        
        elif action == 'delete_item':
            item_id = int(request.form['item_id'])
            for i, item in enumerate(menu_data['items']):
                if item['id'] == item_id:
                    # Delete associated image
                    if item['image']:
                        image_path = os.path.join(app.config['UPLOAD_FOLDER'], item['image'])
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    
                    # Remove item
                    menu_data['items'].pop(i)
                    flash('Item deleted successfully', 'success')
                    break
        
        save_client_data(clientname, menu_data)
    
    return render_template('admin.html', menu=menu_data, clientname=clientname, token=token)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)