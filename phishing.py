import json
from collections import Counter
from utils import *
import sys
import requests
from bs4 import BeautifulSoup
import re
# Put in the username and password into infos list. 
# in the format of tuples likes (username, password)
infos = []
curr_accont = 0
username = infos[curr_accont][0]
password = infos[curr_accont][1]

HOMEPAGE_URL = 'https://www.linkedin.com'
LOGIN_URL = 'https://www.linkedin.com/uas/login-submit'
headers = {
    'User-Agent':
    'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0'
}

def get_subbed_html1(conn, bait, user, pmk):
    """
    It substitute the blanks in the html to the wanted information, and return the final string
    """
    with open('./templates/connection_activity/prefix.html', 'r') as fh:
        template = fh.read()

    with open('./templates/connection_activity/pavs.html', 'r') as fh:
        pav_tmp = fh.read()

    linkedin = "https://www.unsw.edu.au"
    see_all = "https://ww.youtube.com"
    pavs = ''

    for person in pmk:
        pavs += pav_tmp.format(person.name, person.img, person.job, person.link)

    template = template.format(conn.name, conn.link, user.name, user.job, conn.img, bait.name, bait.job, bait.link, bait.img, see_all, linkedin, pavs)
    return template

def get_subbed_html2(bait, user):
    """
    It substitute the blanks in the html to the wanted information, and return the final string
    """
    with open('./templates/invitation.html', 'r') as fh:
        template = fh.read()

    with open('./templates/invitation_head.html', 'r') as fh:
        prefix = fh.read()


    template = prefix + template.format(bait.name, int(random_base(3, 3)), bait.job, int(random_base(7, 5)), bait.img, user.name,)
    return template

def get_ordered_endorsers(pairs):
    """
    Return the person that endorsed the most (only considering at most top three skills)
    """
    max_skill_index = min(3, len(pairs))
    seen_cnt = Counter()
    id_dict = dict()


    # count number of
    for skill_pair in pairs[:max_skill_index]:
        for endorser in skill_pair[1]:
            seen_cnt[endorser.id_] += 1
            id_dict[endorser.id_] = endorser

    res = []
    for cnt in seen_cnt.most_common():
        res.append(id_dict[cnt[0]])

    print(seen_cnt.most_common())
    return res

def pair_to_people(pairs):
    people = []
    visited = set()
    for pair in pairs:
        for endorser in pair[1]:
            if endorser.id_ not in visited:
                people.append(endorser)
                visited.add(endorser.id_)
    return people[:5]

def generate_html(profile_url):
    spider = rq_scraper(profile_url)
    owner = spider.get_profile_info(profile_url)

    # pairs is a list of items like [skill, [endorsements]]
    pairs = spider.get_skill_with_endorsers(profile_url)

    # get a ordered list of endorsers
    conns = get_ordered_endorsers(pairs)

    # I can get second person either from PAV, or from skills
    # And I need to consider the situation where that person doesnt have these info available
    for i,conn in enumerate(conns):
        print("selected CONN", conn)

        new_pairs = spider.get_skill_with_endorsers(conn.link)

        if new_pairs is not None:
            # TODO need to selectively find people you may know section (at least exclude known person)

            new_pairs = spider.get_skill_with_endorsers(conn.link)
            most_connected = get_ordered_endorsers(new_pairs)
            html1 = get_subbed_html1(conn, most_connected[0], owner, most_connected[1:6])
            html2 = get_subbed_html2(most_connected[0], owner)
            break

    with open('bait.html', 'w') as fh:
       fh.write(html1)

    with open('bait_invite.html', 'w') as fh:
        fh.write(html2)


class rq_scraper:
    def __init__(self, profile_url):
        self.root = profile_url

        # default values
        self.is_logged_in = False
        self.connections = []

        # set up session client
        self.client = requests.Session()
        self.client.headers.update(headers)

    def __login(self):
        """
        Login to linkedin with request session client
        """


        global curr_accont
        global infos
        print("Starting to log in for scraping PAV info")

        response = self.client.get(HOMEPAGE_URL)
        while not self.is_logged_in:
            print(curr_accont + 1, '/', len(infos))
            if curr_accont >= len(infos):
               sys.exit("Can't Login, run out of accounts")

            random_sleep(2, 3)

            bs_obj = BeautifulSoup(response.content, 'lxml')
            csrf = bs_obj.find(id="loginCsrfParam-login")['value']


            login_information = {
                'session_key': infos[curr_accont][0],
                'session_password': infos[curr_accont][1],
                'loginCsrfParam': csrf
            }
            print(login_information)

            self.client.post(LOGIN_URL, data=login_information)
            random_sleep(1, 3)

            # check if really logged in
            # If logged in, then it shouldn't show csrf token again in html
            response = self.client.get(HOMEPAGE_URL)
            bs_obj = BeautifulSoup(response.content, 'lxml')

            if not bs_obj.find(id="login-email") is None:
                print("Not logged in yet")
                curr_accont += 1
            else:
                self.is_logged_in = True
                print('Logged In')

    def __set_cookies_and_header(self, profile_url):
        """
        Set profile_url into the header, and set the csrf token
        """
        # Set profile url to referer
        self.client.headers['referer'] = quote_https(profile_url)

        # find the csrf token (JSESSIONID)
        csrf = self.client.cookies.get_dict()['JSESSIONID'].replace('"', '')

        # set csrf into the header
        self.client.headers['csrf-token'] = csrf

    def __get_skill_link(self, profile_url):
        """
        get the json file address for the featured skill
        """
        prefix = "https://www.linkedin.com/voyager/api/identity/profiles/"
        postfix = "/featuredSkills?includeHiddenEndorsers=true&count=50"
        res = prefix + tr_link(profile_url) + postfix
        return res

    def __get_img(self, person):
        """
        Get the profile image of the person from dictionary
        """
        prefix = "https://media.licdn.com/mpr/mpr/shrinknp_100_100"
        # print(person.get('picture', "NO PICTURE ELEMENT"))

        if 'picture' not in person:
            # print("NONE IMG")
            # print(person)
            return "https://static.licdn.com/scds/common/u/images/email/phoenix/icons/ghost_phoenix_person_100x100_v1.png"
        res =  prefix + person['picture']['com.linkedin.voyager.common.MediaProcessorImage']['id']
        # print(res)
        return res

    def get_entity_urn(self, urn):
        start_index = len("urn:li:fs_endorsedSkill:(")
        end_index = urn.find(',')
        link = urn[start_index: end_index]
        id = urn[end_index+1: -1]
        print(link)
        return (link, id)

    def get_endorser_link(self, urn):
        prefix = "https://www.linkedin.com/voyager/api/identity/profiles/"
        middle = "/endorsements?count=20&includeHidden=true&pagingStart=0&q=findEndorsementsBySkillId&skillId="
        res = prefix + urn[0] + middle + urn[1]
        print(res)
        return res

    def get_endorser_from_json(self, json_obj):
        endorsers = []
        for person in json_obj['elements']:
            endorser_info = person['endorser']['miniProfile']
            endorser_name = ' '.join([endorser_info['firstName'], endorser_info['lastName']])
            endorser_img = self.__get_img(endorser_info)
            endorser_id = endorser_info['publicIdentifier']
            endorser_link = "https://www.linkedin.com/in/" + endorser_id
            endorser = Person(name=endorser_name, job=endorser_info['occupation'], id_=endorser_id, img=endorser_img, link=endorser_link)
            endorsers.append(endorser)

        return endorsers

    def get_skill_with_endorsers(self, profile_url, max_skills=5):
        js_obj = self.get_skill(profile_url)

        if js_obj is None:
            return None

        # item contains skill id, skill name
        skill_endorser_pairs = []
        for i, item in enumerate(js_obj['elements']):
            if i >= max_skills:
                break

            skill_name = item['skill']['name']
            entity_urn = self.get_entity_urn(item['entityUrn'])
            endorser_link = self.get_endorser_link(entity_urn)

            endorser_json = json.loads(self.client.get(endorser_link).content)
            endorsers = self.get_endorser_from_json(endorser_json)

            # Only append when it is larger than 0
            if len(endorsers) > 0:
                skill_endorser_pairs.append([skill_name, endorsers])

        return skill_endorser_pairs

    def get_skill(self, profile_url):
        """
        get skills of a person, then return the skill list
        """
        if not self.is_logged_in:
            self.__login()

        self.__set_cookies_and_header(profile_url)

        skill_link = self.__get_skill_link(profile_url)
        res = self.client.get(skill_link)

        if res.status_code != 200:
            print("skill PAGE REQUEST FAILED", res.status_code)
            return None

        js_obj = json.loads(res.content)
        return js_obj

    def get_profile_info(self, profile_url):
        """
        Get the entry profile's information, it can only be obtained through
        selenium package

        """
        global curr_accont
        if not self.is_logged_in:
            self.__login()

        res = self.client.get(profile_url)

        # TODO Should make it auto re-login for multiple times, currently only once
        print(res.status_code)
        if res.status_code != 200:
            print("PAGE REQUEST FAILED", res.status_code)

            # If fetching page not successful, try get a new account to do it
            curr_accont += 1
            self.is_logged_in = False
            self.__login()
            res = self.client.get(profile_url)

            if res.status_code != 200:
                return None

        content = res.text.replace("&quot;", '"')
        pattern = re.compile('(\{[^\{]*?profile\.Profile"[^\}]*?\})')
        profile_txt = ' '.join(re.findall(pattern, content))

        firstname = re.findall('"firstName":"(.*?)"', profile_txt)
        lastname = re.findall('"lastName":"(.*?)"', profile_txt)
        job = re.findall('"headline":"(.*?)"', profile_txt)


        if firstname and lastname:
            profile_name = ' '.join([firstname[0], lastname[0]])

        profile_info = Person(
            id_=tr_link(profile_url),
            link=profile_url,
            job=job if not job else job[0],
            name=profile_name,
            )

        print(profile_info)
        return profile_info


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./program target_profile_link(include http)")
        exit(1)

    generate_html(sys.argv[1])


