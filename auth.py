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
    "xe64nqmzhcjlct2sux64gslxbhjiequmfdrnantyrhy3cz3ulv7q_",  # Adam@BGE
    "saagukw4hkjf32ap7q6yo6qyragkhutqzfdbt4tkbsc3f2ijkrbq_",  # ilike3pancakes@BGE
    "3bmbut27mwog55bsvuoqegsovst6wtxj73xxap23u372av7jmapq_",  # Yunowho@Morgue
    "jta4edxe5pvlomo5w4kcs66u4ebp5w6bhudqzwrubjwtijar3pyq_",  # Cassidy@Morgue
    "tzuur2ypbupwescn2or5fkmanysn3g3z7bjxhemvpw6f3maichuq_",  # Ready@Morgue
    "el34fwo2s4gkl7wa34ednxgw36z6v7cgt7y7j3qqzszhd5di5s4a_",  # Polly@Morgue
    "mfcvv4xcmtu7wek45idwtrf5mnk4orm4d62dho4s5uxhzhuongnq_",  # Spotty@Blackgate Peni
    "w65qexc2tbqftj53syyaq6ejfd3u3fywxxef32sdyqu7c7ytwleq_",  # ilike3pqncakes@poem
    "w3xf2uyxw7nliybn6y4w4boqhbusyup5ifjy6ahtfwmlqgt4wlfq_",  # Nobody@poem
    "kk3go7fwr4niuydyckp6b54kqz62sbh7gm4tl4tyxpcvyczun6pq_",  # Sira@Morgue
    "v32t7cqoj3syalzsajcg6szbah3i3p4nxdmnjo6y6nilenur7n3q_",  # Eric@BGE
    "nz5rw5l5z5goepyvugvmfn7opjpeufmem75d2d4q4dej3l7s2uxa_",  # Blas#Morgue
    "tgd2yc43fejlxduc4aortmiwruolj7rwlnfjk5prenqjdewddhiq_",  # ilike3pancakes@sinoclock
    "hmvrgi7tpv5by6qqk252khwednv5zlwxd3kiyuzqrnjjcra67boq_",  # Kat@sinoclock
    "wwafkxej3w4hlobauwcyhopmeudw4lfoqr2eqeh7sril6yijouea_",  # wetter@sinoclock
    "6gbvbz4budh7yhwxsijjdklyka7klats3bhsh6lh4aspzfywi44q_",  # wetter@coven
    "zkw2ncbf7euiilw4iguwwtkemrhrnpgrqynaa3y7afwhef7mtpoq_",  # ilike3pancakes@coven
    "s4nhz3mnkieoofjr7kmui5wxaaxpongfaj7ezgp4pkdan66fh7aa_",  # Rompe@morgue
    "2cgtgby2hjsyqf7ec3m6iwkgrn5mmqieaigporcaywhme6t5uncq_",  # Boney@WeeklyGroup
    "xfouihqbab7z4gj22c4tnwczhs42k3jcxfefxv2gjhhlbcqmj56a_",  # ilike3pancakes@WeeklyGroup
}


def auth(user_jid: str) -> bool:
    return any(user_jid.startswith(prefix) for prefix in admin_from_jid_prefixes)


if __name__ == "__main__":
    assert auth("ilike3pancakes0_xyz")
    assert not auth("someuser_123")
    print("Ok")
