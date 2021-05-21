import os

from quarry.net.auth import Profile
from quarry.net.client import ClientFactory
from twisted.internet import defer, reactor


@defer.inlineCallbacks
def main():
    print("logging in...")
    profile = yield Profile.from_credentials(
        os.environ['MOJANG_USERNAME'], os.environ['MOJANG_PASSWORD'])
    factory = ClientFactory(profile)
    print("connecting...")
    yield factory.connect("localhost", 25565)
    print("connected!")


if __name__ == "__main__":
    main()
    reactor.run()
