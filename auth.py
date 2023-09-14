admin_from_jid_prefixes = {
    "ilike3pancakes0_",
    "c7mjfxiow6r43yxlpxtxuomgddwcj4wkaqdpcgb6lckg3arw6ewq_",  # ilike3pancakes
    "od67rvy7hl5sya76cx2ivacapijhz5apc2kwprgqfxywk3ako6ba_",  # ilike3pancakes
    "7j4s5a3z5dsdjwsdnx2el3nr53kjuolqbigpazfwsqvk54jxwoha_",  # Moon@The Morgue
    "c7sj2xtp6z6uahigubffp5smvexsokbqywnbzoxxbv5qsb3z7jda_",  # Spike@The Morgue
    "6jjr2tkf4qecstvvws564gf4wtvfl2ogjlvmppfzqlqlkaclnemq_",  # Wetter@The Morgue
    "z4cexwlkzibakpaulcgluflkvmwfzinnfadyk3unydkcfa633wma_",  # Tom@The Morgue
    "fm6b47vgnbk6pjhitgrhzsxwoov5bh5retv5vvxskgt42di2jgmq_",  # Schizo@The Morgue
    "tlyvcx66njflcusrcqihzk6fbkt4bfcmlgaq57t7lo6obiy5fywq_",  # ilike3pancakes@Children of the ni
    "vgs5pqqa7csobgks6uqd3qev2ncoe54mmqx2qrwefee4afa57wtq_",  # DisturbedBurger@Dope Memes
    "jxlswh5ml6qbkm6ditnwdz6s4itwnz22ugr73nky7mk73zvk3s6a_",  # ilike3pancakes@Dope Memes
    "kggv6poplly7eqoc4tup3uaebxbydi3tbpe2s7ew67w3s4256tlq_",  # Khelle@The Morgue
    "xe64nqmzhcjlct2sux64gslxbhjiequmfdrnantyrhy3cz3ulv7q_",  # Adam@BGE
    "saagukw4hkjf32ap7q6yo6qyragkhutqzfdbt4tkbsc3f2ijkrbq_",  # ilike3pancakes@BGE
    "3bmbut27mwog55bsvuoqegsovst6wtxj73xxap23u372av7jmapq_",  # Yunowho@Morgue
    "s3rmebr7hg2rfutfwlm6dqi43757gerl4elaafqysunlelz5mlkq_",  # Lyserga@Morgue
    "jta4edxe5pvlomo5w4kcs66u4ebp5w6bhudqzwrubjwtijar3pyq_",  # Cassidy@Morgue
    "tzuur2ypbupwescn2or5fkmanysn3g3z7bjxhemvpw6f3maichuq_",  # Ready@Morgue
    "el34fwo2s4gkl7wa34ednxgw36z6v7cgt7y7j3qqzszhd5di5s4a_",  # Polly@Morgue
    "mfcvv4xcmtu7wek45idwtrf5mnk4orm4d62dho4s5uxhzhuongnq_",  # Spotty@Blackgate Peni
    "5dakspl22ohponzu2fdycazjow3hrzmpffza3hhg6yabdi25uqsa_",  # Khelle@Hell
    "ywa5jykdafzyfxgq2zzlqedvpfabciqm473eecmxzp4vy7ctsjga_",  # Cide@Hell
    "lyd3kedas6qjice5x2esi6mrfyqqvc3fjqadxmbcsc26xq3rdysq_",  # ilike3pancakes@Hell
    "poklg7x4wx3j3tr4zlvyrnajyxilz7xdhr45yo3ccirwjf7pqg6q_",  # David@Hell
    "w65qexc2tbqftj53syyaq6ejfd3u3fywxxef32sdyqu7c7ytwleq_",  # ilike3pqncakes@poem
    "w3xf2uyxw7nliybn6y4w4boqhbusyup5ifjy6ahtfwmlqgt4wlfq_",  # Nobody@poem
    "kk3go7fwr4niuydyckp6b54kqz62sbh7gm4tl4tyxpcvyczun6pq_",  # Sira@Morgue
    "v32t7cqoj3syalzsajcg6szbah3i3p4nxdmnjo6y6nilenur7n3q_",  # Eric@BGE
    "abp5ysnmxbrutb7sr7ibpowq74ejn2h4pgnqrrxab37ac2kcsi4a_",  # Blas@Hell
}


def auth(user_jid: str) -> bool:
    return any(user_jid.startswith(prefix) for prefix in admin_from_jid_prefixes)


if __name__ == "__main__":
    assert auth("ilike3pancakes0_xyz")
    assert not auth("someuser_123")
    print("Ok")
