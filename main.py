from flask import Flask, render_template, redirect, url_for, jsonify, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL
from flask_sqlalchemy import SQLAlchemy
from random import choice

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class CafeForm(FlaskForm):
    name = StringField('Cafe name', validators=[DataRequired()])
    map_url = StringField('Cafe location on Google Maps(URL)', validators=[DataRequired(), URL()])
    img_url = StringField('Cafe image(URL)', validators=[DataRequired(), URL()])
    location = StringField('Cafe location', validators=[DataRequired()])
    sockets = SelectField('Power sockets availability', validators=[DataRequired()],
                          choices=['True', 'False'])
    toilet = SelectField('Toilet availability', validators=[DataRequired()],
                         choices=['True', 'False'])
    wifi = SelectField('Wifi availability', validators=[DataRequired()],
                       choices=['True', 'False'])
    calls = SelectField('Calls availability', validators=[DataRequired()],
                        choices=['True', 'False'])
    seats = SelectField('Seats availability', validators=[DataRequired()],
                        choices=['0-10', '10-20', '20-30', '30-40', '50+'])
    price = StringField('Cafe price', validators=[DataRequired()])
    submit = SubmitField('Submit')


# Caffe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/cafes')
def cafes():
    all_cafes = db.session.query(Cafe).all()
    return render_template('cafes.html', cafes=all_cafes)


@app.route('/add', methods=["GET", "POST"])
def add_cafe():
    form = CafeForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
            name=form.name.data,
            map_url=form.map_url.data,
            img_url=form.img_url.data,
            location=form.location.data,
            has_sockets=bool(form.sockets.data, ),
            has_toilet=bool(form.toilet.data, ),
            has_wifi=bool(form.wifi.data, ),
            can_take_calls=bool(form.calls.data, ),
            seats=form.seats.data,
            coffee_price=form.price.data,
        )
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for('cafes'))
    return render_template('add.html', form=form)


# API
@app.route("/api/random")
def get_random_cafe():
    all_cafes = db.session.query(Cafe).all()
    random_cafe = choice(all_cafes)
    return jsonify(cafe=random_cafe.to_dict())


@app.route("/api/all_cafes")
def get_all_cafes():
    all_cafes = db.session.query(Cafe).all()
    return jsonify(cafe=[cafe.to_dict() for cafe in all_cafes])


@app.route("/api/search")
def search():
    location = request.args.get("loc")
    cafe_in_location = Cafe.query.filter_by(location=location).all()
    if not cafe_in_location:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."})
    else:
        return jsonify(cafe=[cafe.to_dict() for cafe in cafe_in_location])


@app.route("/api/add", methods=["POST"])
def post_new_cafe():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets")),
        has_toilet=bool(request.form.get("toilet")),
        has_wifi=bool(request.form.get("wifi")),
        can_take_calls=bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})


@app.route("/api/update-price/<int:cafe_id>", methods=["GET", "PATCH"])
def patch_cafe(cafe_id):
    new_price = request.args.get("new_price")
    cafe_to_update = Cafe.query.get(cafe_id)
    if cafe_to_update is None:
        return jsonify(error={"Not Found": "Sorry, we don't have this cafe."}), 404
    else:
        cafe_to_update.coffee_price = new_price
        db.session.commit()
        return jsonify(response={"success": "Successfully updated cafe."}), 200


@app.route("/api/report-closed/<int:cafe_id>", methods=["GET", "DELETE"])
def delete_cafe(cafe_id):
    api = request.args.get("api-key")
    cafe_to_delete = Cafe.query.get(cafe_id)
    if api == "TopSecretAPIKey" and cafe_to_delete is not None:
        db.session.delete(cafe_to_delete)
        db.session.commit()
        return jsonify(response={"success": "Successfully deleted cafe."}), 200
    elif api != "TopSecretAPIKey":
        return jsonify(error={"Wrong api-key": "Sorry, you don't have access"}), 403
    else:
        return jsonify(error={"no such caffe": "Sorry, we don't have this caffe"}), 403


if __name__ == '__main__':
    app.run(debug=True)
