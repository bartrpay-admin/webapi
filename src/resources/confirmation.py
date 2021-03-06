# flask
from flask import request, url_for, make_response, render_template

# flask_restful
from flask_restful import Resource

# models
from models.production.confirmation import ConfirmationModel
from models.production.user import UserModel

# mailgun
# from libs.mailgun import MailGunException

# traceback
import traceback

# method to change the status of a confirmation to confirmed
class Confirmation (Resource):

    @classmethod
    def get(cls, confirmation_id: str):

        # find confirmation by id
        confirmation = ConfirmationModel.find_by_id(confirmation_id)

        headers = {
            "Content-Type": "text/html"
        }

        # Nor found
        if confirmation is None:
            return make_response(
                render_template(
                    "not_found.html"
                ),
                404,
                headers
            )

        # Confirmartion expired
        if confirmation.expired:
            link = request.url_root[:-1] + url_for(
                "auth.confirmationbyuser", user_id=confirmation.user.id
            )
            return make_response(
                render_template("resend_confirmation_template.html",
                                message=f"Your confirmation has expired! To resend confirmation email click", link=link),
                400,
                headers
            )

        # Already confirmed
        if confirmation.confirmed:
            return make_response(
                render_template(
                    "info_template.html", message="Your confirmation is already confirmed !"),
                200,
                headers
            )

        # Confirm
        confirmation.confirmed = True
        confirmation.save_to_db()

        return make_response(
            render_template(
                "confirmation_page.html", email=confirmation.user.email
            ),
            200,
            headers)


class ConfirmationByUser(Resource):

    # @classmethod
    # def get(cls, user_id: int):
    #     """
    #     This endpoint is used for testing and viewing Confirmation models and should not be exposed to public.
    #     """
    #     user = UserModel.find_by_id(user_id)
    #     if not user:
    #         return {"message": gettext("user_not_found")}, 404
    #     return (
    #         {
    #             "current_time": int(time()),
    #             # we filter the result by expiration time in descending order for convenience
    #             "confirmation": [
    #                 confirmation_schema.dump(each)
    #                 for each in user.confirmation.order_by(ConfirmationModel.expire_at)
    #             ],
    #         },
    #         200,
    #     )

    @classmethod
    def get(cls, user_id):

        # find user by id
        user = UserModel.find_by_id(user_id)

        headers = {
            "Content-Type": "text/html"
        }

        if not user:
            return make_response(
                render_template("not_found.html"),
                404,
                headers
            )

        try:
            confirmation = user.most_recent_confirmation

            if confirmation:
                if confirmation.confirmed:
                    return make_response(
                        render_template(
                            "info_template.html", message="Already confirmed!"),
                        200,
                        headers
                    )

                confirmation.force_to_expire()

            # create a new confirmation
            new_confirmation = ConfirmationModel(user_id)
            new_confirmation.save_to_db()

            # send an email
            # user.send_confirmation_email()

            return make_response(
                render_template(
                    "info_template.html", message="Email sent!"),
                200,
                headers
            )

        # except MailGunException as e:
        #     return {"message": str(e)}, 500
        except:
            traceback.print_exc()
            return {"message": "Error"}, 500
