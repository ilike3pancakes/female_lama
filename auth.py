admin_from_jid_prefixes = {
    "ilike3pancakes0_",
    "c7mjfxiow6r43yxlpxtxuomgddwcj4wkaqdpcgb6lckg3arw6ewq_",  # ilike3pancakes
    "od67rvy7hl5sya76cx2ivacapijhz5apc2kwprgqfxywk3ako6ba_",  # ilike3pancakes
    "cg6ofxmwwf6gp4ycc6quq6gy4yffdlimgezpsq33myvrfrwlo4sa_",  # ilike3pancakes@The Lounge
    "7j4s5a3z5dsdjwsdnx2el3nr53kjuolqbigpazfwsqvk54jxwoha_",  # Moon@The Morgue
    "c7sj2xtp6z6uahigubffp5smvexsokbqywnbzoxxbv5qsb3z7jda_",  # Spike@The Morgue
    "6jjr2tkf4qecstvvws564gf4wtvfl2ogjlvmppfzqlqlkaclnemq_",  # Wetter@The Morgue
    "z4cexwlkzibakpaulcgluflkvmwfzinnfadyk3unydkcfa633wma_",  # Tom@The Morgue
    "vm2dlmgnplwmjn7qmhmav7f24pyuezdeminvqehponpkoz65hlsa_",  # Rick@The Lounge
    "5p3lulvmvogf2i6cya7tarhx3pmzqw5htnx2hbtecnh5h4q2poja_",  # Stitch@The Lounge
    "3bxyg6npg6a4prg5uk3jd34mpbgfamzr6eomznzd2hssm2ekuuea_",  # Boney@The Lounge
    "fm6b47vgnbk6pjhitgrhzsxwoov5bh5retv5vvxskgt42di2jgmq_",  # Schizo@The Morgue
    "tlyvcx66njflcusrcqihzk6fbkt4bfcmlgaq57t7lo6obiy5fywq_",  # ilike3pancakes@Children of the ni
    "vgs5pqqa7csobgks6uqd3qev2ncoe54mmqx2qrwefee4afa57wtq_",  # DisturbedBurger@Dope Memes
    "jxlswh5ml6qbkm6ditnwdz6s4itwnz22ugr73nky7mk73zvk3s6a_",  # ilike3pancakes@Dope Memes
    "kggv6poplly7eqoc4tup3uaebxbydi3tbpe2s7ew67w3s4256tlq_",  # Khelle@The Morgue
    "xe64nqmzhcjlct2sux64gslxbhjiequmfdrnantyrhy3cz3ulv7q_",  # Adam@BGE
    "saagukw4hkjf32ap7q6yo6qyragkhutqzfdbt4tkbsc3f2ijkrbq_",  # ilike3pancakes@BGE
    "3bmbut27mwog55bsvuoqegsovst6wtxj73xxap23u372av7jmapq_",  # Yunowho@Morgue
    "s3rmebr7hg2rfutfwlm6dqi43757gerl4elaafqysunlelz5mlkq_",  # Lyserga@Morgue
}


def auth(user_jid: str) -> bool:
    return any(user_jid.startswith(prefix) for prefix in admin_from_jid_prefixes)


if __name__ == "__main__":
    assert auth("ilike3pancakes0_xyz")
    assert not auth("someuser_123")
    print("Ok")
