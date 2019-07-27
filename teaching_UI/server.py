from flask import Flask, flash, request, render_template, jsonify, redirect
from flask_socketio import socketio
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField
from wtforms.validators import Required, InputRequired, DataRequired

'''
Teaching User Interface
'''


app = Flask(__name__, template_folder='static/templates')
app.config['SECRET_KEY'] = 'secret!'


name = "subject1"



constraint_names = ["time_limit", "flying_speed", "update_freq", "fly_village", "fly_water", "tank_dist", "radar_dist"]
folder_path = "../../tasking-constraint-learning/demo_dataset/user_data/"

# constraints form
class constraintsForm(FlaskForm):

    time_limit = RadioField('Time limit:',
            choices=[('short','Short'),('long','Long'), ('None','None')])

    flying_speed = RadioField('Drone flying speed:',
            choices=[('slow','Slow'), ('fast','Fast')])

    update_freq = RadioField('Frequency of sending updates:',
            choices=[('low','Low'), ('high','High')])

    fly_village = RadioField('People min distance:',
            choices=[('low','Low'), ('high','High')])

    fly_water = RadioField('Prohibit flying over water:',
            choices=[('no','No'), ('yes','Yes')])

    tank_dist = RadioField('Minimum distance to tank:',
            choices=[('low','Low'), ('high','High')])

    radar_dist = RadioField('Minimum distance to radar:',
            choices=[('low','Low'), ('high','High')])

    submit = SubmitField('Next')


# redirect to the first experiment
@app.route('/')
def start():
    return redirect('/1')


# the teaching interface with the constraints form, for a specific trial
@app.route('/<trial>', methods=['GET', 'POST'])
def teaching_UI(trial):
    # create form
    consForm = constraintsForm()

    # received form data
    if consForm.validate_on_submit():
        print('Form submitted with data')
        write_result_to_csv(consForm, int(trial))
        return redirect('/' + str(int(trial) + 1))

    if consForm.errors != {}:
        print("Form errors:", consForm.errors)

    return render_template('teaching_UI.html', trial=trial, form=consForm)




def write_result_to_csv(form, trial):
    '''
    Write the constraints specified by the user for a specific trial to a csv file
    '''

    # create and open file
    fl = folder_path + name + ".csv"
    mode = 'w' if trial == 1 else 'a+'
    with open(fl, mode) as f:

        # add constraint names / headers if it is the first trial
        if trial == 1:
            f.write(",".join(constraint_names) + "\n")

        # get form data
        usr_constraints = f"{form.time_limit.data}, {form.flying_speed.data}, \
                            {form.update_freq.data}, {form.fly_village.data}, \
                            {form.fly_water.data}, {form.tank_dist.data}, \
                            {form.radar_dist.data}"

        # write to file
        f.write(f"{usr_constraints.replace(' ','')}\n")
        print(f"Appended trial {trial} data to {fl}")






if __name__ == "__main__":
    print("Server running")
    socketio.run(app, port=3001)
