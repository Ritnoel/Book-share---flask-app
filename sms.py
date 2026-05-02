from random import randint


class Provider:
    """A SMS Provider to send verification-codes"""

    def __init__(self, company: str):
        """_summary_

        Args:
            company (str): Send SMS in the name of the given company
        """
        self.__codes = {}
        self.__company = company

    def __sms(self, code: str, name: str) -> str:
        return f"""
        +++++++++ SMS SEND TO {name} +++++++++
        Hello {name},

        Your verification code is: {code}

        {self.__company}
        ++++++++++++++++++++++++++++++++++++++++
        """

    def send_verification(self, number : str,  name: str = "Customer") -> int:
        """Send a verification code thru 'fake' SMS

        Args:
            number (str): mobile number
            name (str): name of the customer to great with, otherwise general name 'Customer' is used.
        Returns:
            str: a 6 digit number
        """
        code = randint(100000, 999999)
        self.__codes[number] = code
        print(self.__sms(code, name))
        return code

    def verify_code(self, number: str, code: int) -> bool:
        """Check if the latest code to the given number is correct

        Args:
            number (str): phone number
            code (int): given code by user

        Returns:
            bool: True if the code is correct or False if number is not known or code is incorrect.
        """
        return self.__codes.get(number, False) == code
    
    def remove_number(self, number: str) -> bool:
        """Remove phone number with latest code

        Args:
            number (str): phone number

        Returns:
            bool: True if the number exist in the dictionary
        """
        if self.__codes.get(number, False):
            self.__codes.pop(number)
            return True
        return False


if __name__ == "__main__":
    provider = Provider("LinkedIn")
    code = provider.send_verification("0612345678", "Harry")

    # Check if the code is correct
    if provider.verify_code("0612345678", code):
        print("Number is correct")
    
    # Code is incorrect
    if not provider.verify_code("0612345678", -999999):
        print("Code is not correct or number don't exist")
    
    if provider.remove_number("012345678"):
        print("Number is removed")

    if not provider.remove_number("87654323456"):
        print("Number does don't exist.")


# NOTES

# self — in Python, every method in a class automatically receives the object itself as the first argument. You never pass it manually — Python handles it. So when you call provider.send_verification(phone_number, name), Python automatically passes provider as self behind the scenes.
# name: str = "Customer" — this means:

# name is the parameter name
# : str means it expects a string
# = "Customer" means if you don't pass a name, it defaults to "Customer"