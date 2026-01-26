station = str(input())

next_st = station[:-2] + f"{int(station[-2:])+1:02d}"

print(next_st)